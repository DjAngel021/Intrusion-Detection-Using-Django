from django.http import HttpResponse
from django.shortcuts import render
from django.shortcuts import redirect
# FILE UPLOAD AND VIEW
from  django.core.files.storage import FileSystemStorage
# SESSION
from django.conf import settings
from .models import *
import pandas as pd
import joblib
import os
from sklearn.preprocessing import LabelEncoder
import json
import uuid

# Load ML model and preprocessing objects
import os

MODEL_DIR = os.path.join(settings.BASE_DIR, 'ML')

def load_ml_model():
    """Load the trained model and preprocessing objects"""
    try:
        model_path = os.path.join(MODEL_DIR, 'best_intrusion_detection_model.pkl')
        scaler_path = os.path.join(MODEL_DIR, 'scaler.pkl')
        features_path = os.path.join(MODEL_DIR, 'selected_features.pkl')
        
        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        features = joblib.load(features_path)
        
        return model, scaler, features
    except Exception as e:
        print(f"Error loading ML model: {e}")
        return None, None, None

def predict_from_csv(csv_file_path, model, scaler, features):
    """
    Load data from CSV and make predictions.
    """
    try:
        # Read the CSV file
        raw_data = pd.read_csv(csv_file_path)
        
        # Apply label encoding to object columns
        for col in raw_data.columns:
            if raw_data[col].dtype == 'object' and col != 'class':
                label_encoder = LabelEncoder()
                raw_data[col] = label_encoder.fit_transform(raw_data[col])
        
        # Remove 'class' column if it exists
        if 'class' in raw_data.columns:
            raw_data = raw_data.drop(['class'], axis=1)
        
        # Select only the required features
        data_selected = raw_data[features]
        
        # Scale the data
        data_scaled = scaler.transform(data_selected)
        
        # Make predictions
        predictions = model.predict(data_scaled)
        
        if hasattr(model, 'predict_proba'):
            probabilities = model.predict_proba(data_scaled)
        else:
            probabilities = None
        
        return predictions, probabilities
    except Exception as e:
        print(f"Error during prediction: {e}")
        return None, None
def first(request):
    return render(request,'index.html')

def index(request):
    return render(request,'index.html')



def reg(request):
    return render(request,'register.html')

def addreg(request):
    if request.method=="POST":
        name=request.POST.get('name')
        phone=request.POST.get('phone_number')
        email=request.POST.get('email')
        password=request.POST.get('password')
         
        sa=user(name=name,phone_number=phone,email=email,password=password)
        sa.save()

    return render(request,'index.html',{'message':"Successfully Registered"})

def v_register(request):
    users=user.objects.all()
    return render(request,'v_register.html',{'result':users})

def login(request):
    return render(request,'login.html')

def about(request):
    return render(request, 'about.html')

def addlogin(request):
    email=request.POST.get('email')
    password=request.POST.get('password')
    if email=='admin@gmail.com' and password=='admin':
        request.session['details']='admin'
        return render(request,'index.html')
    elif user.objects.filter(email=email,password=password).exists():
        userdetails=user.objects.get(email=email,password=password)
        request.session['uid']=userdetails.id
        request.session['uname']=userdetails.name
        return render(request,'index.html')
    else:
        print("Invalid username or password")
        return render(request,'login.html',{'message':"Invalid username or password"})

def logout(request):
    session_keys=list(request.session.keys())
    for key in session_keys:
        del request.session[key]
    return redirect(index)

def fedback(request):
    return render(request,'feedback.html')

def addfedbk(request):
    if request.method=="POST":
        a= request.session['uname']
        b=request.POST.get('feedbacks')

        s=feedback(username=a,feedbacks=b)
        s.save()
        return render(request,'feedback.html',{'message':"Thank you for your feedback"})
    
def v_feedback(request):
     e=feedback.objects.all()
     return render(request,'view_feedback.html',{'result':e})

def file(request):
    return render(request,'upload.html')

def addfile(request):
    if request.method=="POST":
        user_name=request.session['uname']
        file=request.FILES['file']
       
        # Read CSV and display contents without saving file
        try:
            # Read CSV directly from uploaded file
            df = pd.read_csv(file)
            
            # Convert dataframe to JSON for session storage (avoid outer list when single row)
            csv_records = json.loads(df.to_json(orient='records'))
            if isinstance(csv_records, list) and len(csv_records) == 1:
                csv_data_json = json.dumps(csv_records[0])  # store single object without brackets
            else:
                csv_data_json = json.dumps(csv_records)
            
            # Store CSV data in session (not the file)
            request.session['csv_data'] = csv_data_json
            request.session['csv_filename'] = file.name
            
            # Convert dataframe to HTML table for preview
            csv_preview = df.head(20).to_html(classes='table table-striped table-bordered table-hover', index=False)
            
            return render(request, 'upload.html', {
                'message': f"Data loaded successfully from {file.name}. Review the data below and click 'Predict' to analyze.",
                'csv_preview': csv_preview,
                'csv_rows': len(df),
                'csv_columns': len(df.columns),
                'show_predict_button': True
            })
        except Exception as e:
            return render(request, 'upload.html', {
                'error': f"Error reading CSV file: {str(e)}"
            })
    
    return render(request,'upload.html')

def predict_and_save(request):
    """Handle prediction and save to database"""
    if request.method=="POST":
        user_name = request.session.get('uname')
        csv_data_json = request.session.get('csv_data')
        #csv_filename = request.session.get('csv_filename', 'data.csv')
        
        if not csv_data_json:
            return render(request, 'upload.html', {
                'error': "No data found. Please upload a file first."
            })
        
        try:
            # Reconstruct DataFrame from session data (supports single-object JSON without brackets)
            parsed = json.loads(csv_data_json)
            if isinstance(parsed, dict):
                parsed = [parsed]
            df = pd.DataFrame(parsed)
            
            # Create a temporary CSV file for prediction
            temp_filename = f"temp_{user_name}_{uuid.uuid4().hex}.csv"
            fs = FileSystemStorage()
            temp_file_path = os.path.join(settings.MEDIA_ROOT, temp_filename)
            df.to_csv(temp_file_path, index=False)
            
            # Load ML model
            model, scaler, features = load_ml_model()
            
            prediction_result = "Unknown"
            prediction_details = ""
            anomaly_count = 0
            normal_count = 0
            
            if model is not None and scaler is not None and features is not None:
                try:
                    # Make predictions
                    predictions, probabilities = predict_from_csv(temp_file_path, model, scaler, features)
                    
                    if predictions is not None:
                        # Count normal and anomaly
                        anomaly_count = int((predictions == 0).sum())
                        normal_count = int((predictions == 1).sum())
                        
                        # Determine overall result
                        if anomaly_count > normal_count:
                            prediction_result = "Anomaly Detected"
                        else:
                            prediction_result = "Normal"
                        
                        prediction_details = f"Normal: {normal_count}, Anomaly: {anomaly_count}"
                except Exception as e:
                    prediction_result = f"Error: {str(e)}"
                    prediction_details = "Failed to process data"
            else:
                prediction_result = "Model Not Loaded"
                prediction_details = "ML model files not found"
            
            # Delete temporary CSV file after prediction
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

            print("\n\nJSON Data:", csv_data_json)
            #print("\n\nJSON Data:", list(csv_data_json)[0])
            
            # Save JSON data content to database
            cus = fileupload(
                username=user_name,
                data=csv_data_json,
                result=prediction_result
            )
            cus.save()
            
            # Clear session data
            if 'csv_data' in request.session:
                del request.session['csv_data']
            if 'csv_filename' in request.session:
                del request.session['csv_filename']
            
            return render(request, 'upload.html', {
                'success_message': f"Prediction completed and saved successfully!",
                'prediction': prediction_result,
                'prediction_details': prediction_details
            })
            
        except Exception as e:
            return render(request, 'upload.html', {
                'error': f"Error during prediction: {str(e)}"
            })
    
    return redirect('file')
    
def v_addfile(request):
    v=fileupload.objects.all()
    return render(request,'view_file.html',{'result':v})

def v_addfile_user(request):
    us=request.session['uname']
    v=fileupload.objects.filter(username=us)
    return render(request,'viewuserfile.html',{'result':v})