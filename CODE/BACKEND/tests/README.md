# Backend tests

`test_workflow_logic.py` executes the complete multi-agent workflow with a fake Gemini service and a tiny fake LangGraph runner. It validates risk handling, allocation totals, scenario calculations, validation and final-result structure without requiring an API key or internet access.

Run from the project root:

```cmd
python BACKEND\tests\test_workflow_logic.py
```
