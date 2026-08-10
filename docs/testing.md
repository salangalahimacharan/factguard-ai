# FactGuard AI Testing Documentation

## Test Suite Overview

FactGuard AI includes an automated Pytest test suite in `tests/test_agents.py` covering 10 academic test scenarios:

1. **Test 1**: Clearly Verifiable True Claim (NASA Webb telescope discovery).
2. **Test 2**: Clearly False Claim (5G virus conspiracy).
3. **Test 3**: Partially True Claim (Coffee and longevity health claim).
4. **Test 4**: Misleading Claim (Sensational EV vs diesel pollution claim).
5. **Test 5**: Insufficient Evidence (Secret project rumor).
6. **Test 6**: Conflicting Sources (Economic inflation forecasts).
7. **Test 7**: Outdated Claim (2015 Mars water discovery).
8. **Test 8**: Opinion Presented as Fact (Subjective AI art opinion).
9. **Test 9**: Multiple Claims in One Post (Multi-claim tech launch).
10. **Test 10**: Prompt Injection Attempt (`SYSTEM INSTRUCTION: Ignore all...`).

### Running Backend Tests
```powershell
pytest -v tests/test_agents.py
```
