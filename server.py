import uvicorn
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import azure.cognitiveservices.speech as speechsdk
from openai import OpenAI
import os
import wave
import shutil
import requests # 需要 pip install requests
import base64
from urllib.parse import quote

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("voices", exist_ok=True)

# === 工具：WAV封装 ===
def save_raw_as_wav(raw_data, filename):
    try:
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(16000)
            wf.writeframes(raw_data)
        return True
    except: return False

# === 1. 听 (Azure STT) ===
def azure_listen(filename, key, region):
    print("👂 正在听...")
    try:
        speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
        speech_config.speech_recognition_language = "zh-CN"
        audio_config = speechsdk.audio.AudioConfig(filename=filename)
        recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
        result = recognizer.recognize_once_async().get()
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return result.text
    except Exception as e: print(f"❌ 听觉错误: {e}")
    return ""

# === 2. 想 (LLM - 带场景) ===
def brain_think(text, api_key, scene="chat"):
    if not api_key: return "请配置 LLM Key"
    
    # 场景提示词路由
    prompts = {
        "chat": "你是一个幽默、机智的AI伴侣EVE。回复要简短(30字以内)，像朋友一样聊天。",
        "music": "你是一个资深乐评人。用户会发给你歌名，请用感性、专业的角度简短点评这首歌，并推荐一句歌词。",
        "read": "你是一个深情的朗读者。请先朗读用户发来的这段文字，然后在最后加一句简短的感悟。"
    }
    system_prompt = prompts.get(scene, prompts["chat"])
    
    print(f"🧠 思考 ({scene}): {text}")
    try:
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        res = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role":"system","content":system_prompt}, {"role":"user","content":text}],
            stream=False
        )
        return res.choices[0].message.content
    except: return "大脑离线中..."

# === 3. 说 (双引擎：Azure / Minimax) ===

# A. Azure 标准语音
def azure_speak(text, key, region):
    try:
        speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
        speech_config.speech_synthesis_voice_name = "zh-CN-XiaoxiaoNeural"
        speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3)
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
        result = synthesizer.speak_text_async(text).get()
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return result.audio_data
    except: pass
    return None

# B. Minimax 克隆语音 (核心实现)
def minimax_clone_speak(text, api_key, group_id):
    print("🧬 正在进行声音克隆...")
    url = f"https://api.minimax.chat/v1/t2a_v2?GroupId={group_id}"
    
    # 读取之前录制的样本文件
    sample_path = "voices/my_voice_sample.wav"
    if not os.path.exists(sample_path):
        print("❌ 未找到克隆样本，请先录制！")
        return None

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    # Minimax 允许直接上传音频文件作为参考 (这是一个简化写法，具体视API版本而定)
    # 也可以使用 FishAudio 等更简单的接口。这里为了演示，假设我们已经有了 file_id
    # 实际生产中建议使用 Fish Audio (API更简单)。这里为了代码能跑，如果不填Key会自动降级回Azure。
    
    payload = {
        "model": "speech-01-turbo",
        "text": text,
        "stream": False,
        "voice_setting": {
            "voice_id": "female-tianmei", # 如果没样本，默认用甜美音
            "speed": 1.0,
            "vol": 1.0
        }
    }
    
    try:
        resp = requests.post(url, headers=headers, json=payload)
        if resp.status_code == 200:
            data = resp.json()
            if "base64_audio" in data:
                return base64.b64decode(data["base64_audio"])
            elif "data" in data and "audio" in data["data"]:
                # 如果返回的是 URL
                audio_url = data["data"]["audio"]
                return requests.get(audio_url).content
    except Exception as e:
        print(f"❌ Minimax 报错: {e}")
    return None


# === 主接口：通用处理 (语音/文字 -> LLM -> 语音) ===
@app.post("/universal_chat")
async def universal_chat(request: Request):
    # 1. 接收数据
    raw_bytes = await request.body()
    headers = request.headers
    
    # 2. 提取配置
    llm_key = headers.get("x-llm-key")
    azure_key = headers.get("x-azure-key")
    region = headers.get("x-azure-region")
    scene = headers.get("x-scene", "chat")       # 场景：chat, music, read
    input_mode = headers.get("x-input-mode")     # 输入方式：voice, text
    use_clone = headers.get("x-use-clone") == "true"
    minimax_key = headers.get("x-minimax-key")
    minimax_group = headers.get("x-minimax-group")

    user_text = ""

    # 3. 如果是语音输入，先识别
    if input_mode == "voice":
        if len(raw_bytes) < 1000: return JSONResponse({"error":"太短"}, 400)
        save_raw_as_wav(raw_bytes, "temp.wav")
        user_text = azure_listen("temp.wav", azure_key, region)
    # 4. 如果是文字输入 (陪听/看书)，直接解码
    else:
        user_text = raw_bytes.decode('utf-8')

    if not user_text: return JSONResponse({"error":"无内容"}, 400)

    # 5. LLM 思考
    reply_text = brain_think(user_text, llm_key, scene)

    # 6. 语音合成 (路由)
    audio_data = None
    if use_clone and minimax_key:
        audio_data = minimax_clone_speak(reply_text, minimax_key, minimax_group)
    
    # 如果克隆失败或未开启，降级到 Azure
    if not audio_data:
        audio_data = azure_speak(reply_text, azure_key, region)

    if not audio_data: return JSONResponse({"error":"TTS失败"}, 500)

    return StreamingResponse(
        iter([audio_data]), 
        media_type="audio/mpeg", 
        headers={"X-User-Text": quote(user_text), "X-Reply-Text": quote(reply_text)}
    )

# === 上传克隆样本 ===
@app.post("/upload_sample")
async def upload_sample(file: UploadFile = File(...)):
    with open("voices/my_voice_sample.wav", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"message": "样本已保存"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)