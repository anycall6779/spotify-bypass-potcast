import os
from flask import Flask, request, render_template, send_from_directory, flash, redirect, url_for, Response
from pydub import AudioSegment
from os.path import splitext
import mimetypes 
from urllib.parse import quote
import webbrowser # 웹 브라우저를 열기 위해 import
from threading import Timer # 서버 시작 후 브라우저를 열기 위해 import

# --- 설정 ---
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'flac', 'ogg', 'm4a'}
SILENCE_DURATION_MS = 60 * 1000 # 1분

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER
app.config['SECRET_KEY'] = 'supersecretkey'

# 서버 시작 시 필요한 폴더가 없으면 자동으로 생성
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(PROCESSED_FOLDER):
    os.makedirs(PROCESSED_FOLDER)

# 허용된 파일 형식인지 확인하는 함수
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- 라우트 (웹페이지 주소) 설정 ---
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('파일이 없습니다')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('선택된 파일이 없습니다')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = file.filename.replace('/', '').replace('\\', '')
            original_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            name_part, ext_part = splitext(filename)
            processed_filename = f"{name_part}_bypass_spotify{ext_part}"
            processed_path = os.path.join(app.config['PROCESSED_FOLDER'], processed_filename)
            
            file.save(original_path)
            
            try:
                silence = AudioSegment.silent(duration=SILENCE_DURATION_MS)
                song = AudioSegment.from_file(original_path)
                final_song = silence + song
                
                file_format = filename.rsplit('.', 1)[1].lower()
                final_song.export(processed_path, format=file_format)
                
                return redirect(url_for('download_file', name=processed_filename))

            except Exception as e:
                flash(f'오류 발생: {e}')
                return redirect(request.url)
        else:
            flash('허용되지 않는 파일 형식이거나 파일에 확장자가 없습니다. (mp3, wav, flac 등)')
            return redirect(request.url)

    return render_template('index.html')

@app.route('/downloads/<path:name>')
def download_file(name):
    file_path = os.path.join(app.config['PROCESSED_FOLDER'], name)

    if not os.path.exists(file_path):
        return "파일을 찾을 수 없습니다 (File Not Found).", 404

    with open(file_path, 'rb') as f:
        file_data = f.read()

    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        mime_type = 'application/octet-stream'

    response = Response(file_data, mimetype=mime_type)
    
    encoded_filename = quote(name)
    response.headers.set(
        'Content-Disposition',
        f"attachment; filename*=UTF-8''{encoded_filename}"
    )
    return response

# --- 서버 실행 ---
def open_browser():
      webbrowser.open_new("http://127.0.0.1:8080")

if __name__ == '__main__':
    # 디버그 모드에서 Flask 재시작 시 브라우저가 중복으로 열리는 것을 방지
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        # 서버가 시작된 후 (약 1초 뒤) 브라우저를 엽니다.
        Timer(1, open_browser).start()
    
    app.run(host='0.0.0.0', port=8080, debug=True)
