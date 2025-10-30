from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/webhooks/test")
async def recv(req: Request):
    body = await req.body()
    print("== WEBHOOK RECEIVED ==")
    print("Headers:", dict(req.headers))
    print("Body:", body.decode())
    return {"ok": True}

