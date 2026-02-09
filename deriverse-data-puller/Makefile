.PHONY: demo ingest analytics clean

demo:
	@echo "🚀 Running full Deriverse analytics demo"
	python -m scripts.run_ingestion
	python -m scripts.run_analytics

analytics:
	python -m scripts.run_analytics

clean:
	rm -rf data/analytics/*.csv
