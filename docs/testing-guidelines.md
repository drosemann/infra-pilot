# Testing Guidelines

Diese Seite bietet kurze, wiederverwendbare Templates für Unit- und Integrationstests.

## Grundsätze

- Nutze sprechende Testnamen mit Verhalten im Fokus.
- Halte Tests isoliert (keine Abhängigkeit von Reihenfolge/externem Zustand).
- Vermeide doppelte Assertions derselben Aussage.
- Nutze Parametrisierung bei mehr als 3 ähnlichen Fällen.
- Stelle klare Failure-Messages bereit.

## Unit-Test Template (Python / pytest)

```python
import pytest


@pytest.mark.parametrize(
    "input_value, expected",
    [
        ("basic", "BASIC"),
        ("Prod-1", "PROD-1"),
        ("", ""),
    ],
)
def test_normalize_name_returns_expected_value(input_value, expected):
    # Arrange
    value = input_value

    # Act
    result = normalize_name(value)

    # Assert
    assert result == expected, f"Expected {expected!r} for input {value!r}, got {result!r}"
```

## Unit-Test Template (JavaScript / Jest)

```javascript
describe("normalizeName", () => {
  test.each([
    ["basic", "BASIC"],
    ["Prod-1", "PROD-1"],
    ["", ""],
  ])("returns %s -> %s", (inputValue, expected) => {
    // Arrange
    const value = inputValue;

    // Act
    const result = normalizeName(value);

    // Assert
    expect(result).toBe(expected);
  });
});
```

## Integrationstest Template (Python / pytest)

```python
def test_provision_server_creates_db_record_and_emits_event(db_session, event_bus, api_client):
    # Arrange
    payload = {
        "region": "eu-central",
        "plan": "small",
    }

    # Act
    response = api_client.post("/servers", json=payload)

    # Assert
    assert response.status_code == 201, f"Expected 201, got {response.status_code}"

    created = db_session.query(Server).filter_by(region="eu-central").one()
    assert created.plan == "small", "Expected created server plan to be persisted"

    assert event_bus.contains("server.provisioned"), "Expected provisioning event to be emitted"
```

## Integrationstest Template (Java / JUnit)

```java
@Test
void createServer_persistsServerAndReturns201() {
    // Arrange
    CreateServerRequest request = new CreateServerRequest("eu-central", "small");

    // Act
    ResponseEntity<ServerResponse> response = restTemplate.postForEntity(
        "/servers", request, ServerResponse.class
    );

    // Assert
    assertEquals(201, response.getStatusCode().value(), "Expected HTTP 201 when creating server");

    Optional<Server> created = serverRepository.findByRegion("eu-central");
    assertTrue(created.isPresent(), "Expected created server to be persisted");
    assertEquals("small", created.get().getPlan(), "Expected persisted plan to match request");
}
```
