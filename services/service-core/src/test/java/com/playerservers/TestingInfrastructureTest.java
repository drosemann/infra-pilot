package com.playerservers;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class TestingInfrastructureTest {
    @Test
    void junitAssertjAndSurefireAreAvailable() {
        assertThat("infra-pilot").startsWith("infra").endsWith("pilot");
    }
}
