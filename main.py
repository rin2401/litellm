import uvicorn
import yaml
from fastapi import FastAPI, Request
from typing import Dict, Any
import httpx
import logging

app = FastAPI()

M = {}

client = httpx.AsyncClient()

CONFIG_PATH = "router.yaml"

with open(CONFIG_PATH, "r") as f:
    CONFIG = yaml.safe_load(f)

M = {x["model_name"]: x for x in CONFIG["model_list"]}


@app.post("/v1/chat/completions")
async def chat(data: Dict[Any, Any], request: Request):
    model = data.get("model")
    if model not in M:
        return {"error": 1, "message": "Model not found"}

    params = M[model]["litellm_params"]

    url = params["api_base"] + "/chat/completions"
    headers = {"Authorization": params["api_key"]}

    print("Request:", data)

    res = await client.post(url, json=data, headers=headers, timeout=600)
    res = res.json()

    print("Response:", res)

    return res



@app.post("/v1/completions")
async def chat(data: Dict[Any, Any], request: Request):
    model = data.get("model")
    if model not in M:
        return {"error": 1, "message": "Model not found"}

    params = M[model]["litellm_params"]

    url = params["api_base"] + "/completions"
    headers = {"Authorization": params["api_key"]}

    print("Request:", data)

    res = await client.post(url, json=data, headers=headers, timeout=600)
    res = res.json()

    print("Response:", res)

    return res



@app.get("/v1/models")
async def models(request: Request):
    models = []
    for x in CONFIG["model_list"]:
        models.append({
            "id": x["model_name"],
            "litellm_params": x["litellm_params"]
        })

    return {"data": models}


@app.post("/config/model")
async def new_model(api_base: str = "https://api.together.xyz/v1", model: str = None, api_key:str = "token-abc123"):
    if not model:
        try:
            headers = {"Authorization": api_key}
            res = await client.get(api_base + "/models", headers=headers)
            res = res.json()
            model = res["data"][0]["id"]
        except Exception as e:
            logging.error(e, exc_info=True)

            return {"error": 1, "message": "Model not found"}

    item = {
        "model_name": model,
        "litellm_params": {
            "model": "openai/" + model,
            "api_base": api_base,
            "api_key": api_key,
        }
    }


    M[model] = item
    CONFIG["model_list"] = list(M.values())

    with open(CONFIG_PATH, 'w') as file:
        yaml.dump(CONFIG, file, sort_keys=False)

    return item


@app.delete("/config/model")
async def delete_model(model: str):
    print(model)

    if model not in M:
        return {"error": 1}

    item = M.pop(model)
    CONFIG["model_list"] = list(M.values())

    with open(CONFIG_PATH, 'w') as file:
        yaml.dump(CONFIG, file, sort_keys=False)

    return item


@app.delete("/deploy")
async def delete_model(model_path: str):
    item = {
        "model_path": model_path
    }

    return item

if __name__ == "__main__":
    uvicorn.run(
        "router:app",
        host="0.0.0.0",
        port=30005,
        reload=False,
    )
