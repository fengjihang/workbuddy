from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routes import tender, analysis, bid, compliance, knowledge, files

# 创建所有表
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ZCM 招投标助手", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tender.router)
app.include_router(analysis.router)
app.include_router(bid.router)
app.include_router(compliance.router)
app.include_router(knowledge.router)
app.include_router(files.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/llm-test")
async def llm_test():
    from .llm.openai_compat import OpenAICompatibleLLM
    try:
        llm = OpenAICompatibleLLM()
        result = await llm.chat_complete([
            {"role": "user", "content": "回复一个字：好"}
        ])
        await llm.close()
        return {"ok": True, "model": llm.model, "reply": result}
    except Exception as e:
        return {"ok": False, "error": str(e)}
