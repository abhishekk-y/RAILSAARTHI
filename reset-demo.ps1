$ErrorActionPreference = 'Stop'
Write-Output 'The demo is in-memory; restart the backend to reset scenario state.'
python -c "from backend.app.synthetic import generate_scenario; print('Synthetic seed 42 is ready:', len(generate_scenario(42).tasks), 'tasks')"
