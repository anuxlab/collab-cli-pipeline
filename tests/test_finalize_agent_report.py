from scripts.finalize_agent_report import classify

def test_classifies_memory_pressure():
    code, message = classify("ollama runner log: out of memory while loading model")
    assert code == "MEMORY_PRESSURE"
    assert "RAM" in message

def test_classifies_missing_model_tag():
    code, message = classify("pull failed: manifest not found")
    assert code == "MODEL_TAG_OR_PULL_FAILURE"


def test_success_classification_is_explicit_in_finalizer():
    code, message = classify("all done; no error found")
    assert code == "UNKNOWN_FAILURE"
    assert message
