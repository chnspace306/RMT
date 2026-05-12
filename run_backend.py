import sys
import os

# 确保 backend 路径正确
sys.path.append(os.getcwd())

print("Step 1: Environment ready. No-Pandas mode.", flush=True)

try:
    print("Step 2: Loading app from backend.main...", flush=True)
    from backend.main import app
    print("Step 3: App loaded successfully.", flush=True)

    if __name__ == "__main__":
        import uvicorn
        print("Step 4: Starting server on http://127.0.0.1:8888", flush=True)
        uvicorn.run(app, host="127.0.0.1", port=8888)
except Exception as e:
    print(f"FAILED: {e}", flush=True)
    import traceback
    traceback.print_exc()
