from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "SaleorQA 测试系统后端已启动"}

# 启动命令 (在终端输入): uvicorn app.backend:app --reload