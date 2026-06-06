limpiar:
	cls
	cls

runapp:
	make limpiar
	uv run streamlit run app.py

main:
	make limpiar
	uv run main.py