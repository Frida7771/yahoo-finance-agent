.PHONY: install dev run test clean

# 安装依赖
install:
	pip install -r requirements.txt

# 开发模式运行
dev:
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 生产模式运行
run:
	uvicorn main:app --host 0.0.0.0 --port 8000

# 下载最新 SEC 文件
download-sec:
	python scripts/download_sec_filing.py

# 重建 RAG 索引
rebuild-index:
	curl -X POST http://localhost:8000/api/rag/rebuild-index

# 清理缓存
clean:
	rm -rf __pycache__
	rm -rf backend/__pycache__
	rm -rf backend/routes/__pycache__
	rm -rf tools/__pycache__
	rm -rf utils/__pycache__
	rm -rf data/vector_store

# 测试 API
test-chat:
	curl -X POST http://localhost:8000/api/chat \
		-H "Content-Type: application/json" \
		-d '{"message": "What is Apple stock price?"}'

test-rag:
	curl -X POST http://localhost:8000/api/rag/ask \
		-H "Content-Type: application/json" \
		-d '{"question": "What are the main risk factors for Microsoft?"}'

test-stock:
	curl http://localhost:8000/api/stock/AAPL

