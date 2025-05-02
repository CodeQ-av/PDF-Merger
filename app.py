from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
from PyPDF2 import PdfMerger
import os
import io
import tempfile

app = Flask(__name__)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024  # 25MB max per file
ALLOWED_EXTENSIONS = {'pdf'}
TEMP_FOLDER = tempfile.gettempdir()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return send_file('templates/index.html')

@app.route('/merge', methods=['POST'])
def merge_pdfs():
    # Check if files were uploaded
    if 'pdfs' not in request.files:
        return jsonify({'error': 'No files uploaded'}), 400
    
    files = request.files.getlist('pdfs')
    
    # Validate files
    if len(files) < 2:
        return jsonify({'error': 'Please upload at least 2 PDF files'}), 400
    
    merger = PdfMerger()
    temp_files = []
    
    try:
        for file in files:
            # Check if file is empty
            if file.filename == '':
                return jsonify({'error': 'One of the files is empty'}), 400
            
            # Check if file is allowed
            if not allowed_file(file.filename):
                return jsonify({'error': f'{file.filename} is not a PDF file'}), 400
            
            # Secure filename and save temporarily
            filename = secure_filename(file.filename)
            temp_path = os.path.join(TEMP_FOLDER, filename)
            file.save(temp_path)
            temp_files.append(temp_path)
            
            # Attempt to add to merger (this checks if PDF is valid)
            try:
                merger.append(temp_path)
            except Exception as e:
                return jsonify({'error': f'Invalid PDF file: {filename}', 'details': str(e)}), 400
        
        # Create merged PDF in memory
        output = io.BytesIO()
        merger.write(output)
        output.seek(0)
        
        # Clean up temp files
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
            except:
                pass
        
        # Send merged PDF as response
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='merged.pdf'
        )
    
    except Exception as e:
        # Clean up temp files in case of error
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
            except:
                pass
        
        return jsonify({'error': 'Failed to merge PDFs', 'details': str(e)}), 500
    
    finally:
        merger.close()

if __name__ == '__main__':
    app.run(debug=True)