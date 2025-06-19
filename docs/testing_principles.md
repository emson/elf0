# Testing Principles

## Core Principles

### 1. Test High-Level Behavior, Not Implementation
- Focus on testing what the code does, not how it does it
- Avoid testing internal implementation details
- Test public APIs and interfaces
- Don't test third-party library internals
- Example: Test that a workflow compiles successfully, not the internal structure of the graph

### 2. Maintain Test Independence
- Each test should be self-contained
- Avoid dependencies between tests
- Don't rely on test execution order
- Use fixtures for shared setup
- Example: Create fresh test data for each test case

### 3. Follow the Arrange-Act-Assert Pattern
- Arrange: Set up test data and conditions
- Act: Perform the action being tested
- Assert: Verify the results
- Keep each section clear and focused
- Example: Set up spec → compile workflow → verify result

### 4. Test Real Use Cases
- Test scenarios that users will actually encounter
- Focus on happy paths and common edge cases
- Avoid testing theoretical or unlikely scenarios
- Example: Test valid workflow configurations rather than invalid syntax

### 5. Keep Tests Simple and Clear
- One assertion per test when possible
- Clear test names that describe the scenario
- Descriptive comments for complex setups
- Example: `test_compile_minimal_workflow` instead of `test_graph_creation`

## Best Practices

### 1. Error Handling
- Test expected error cases at the appropriate level
- Don't test error handling of third-party libraries
- Focus on errors that users might encounter
- Example: Test invalid workflow configurations, not internal library errors

### 2. State Management
- Test state transitions and transformations
- Verify state preservation where required
- Test default values and optional fields
- Example: Test workflow state updates and preservation

### 3. Configuration Testing
- Test with minimal valid configurations
- Verify configuration validation
- Test configuration combinations
- Example: Test workflow compilation with minimal valid specs

### 4. Integration Points
- Test integration with external systems at the appropriate level
- Don't test internal details of external systems
- Focus on the contract between systems
- Example: Test workflow execution, not LLM API details

### 5. Documentation and Maintenance
- Keep tests well-documented
- Update tests when requirements change
- Remove obsolete tests
- Example: Update tests when API changes, don't leave broken tests

### 6. CLI Application Testing
- Test CLI applications at the command level, not function level
- Use proper CLI testing frameworks (e.g., Typer's CliRunner)
- Test parameter handling and type consistency
- Handle empty values and optional parameters explicitly
- Example: Test CLI commands with `CliRunner.invoke()` instead of calling functions directly

## Anti-Patterns to Avoid

### 1. Testing Implementation Details
- Don't test private methods
- Don't test internal state
- Don't test third-party library internals
- Example: Don't test LangGraph's internal graph structure

### 2. Over-Specific Tests
- Don't make tests too brittle
- Avoid testing exact string matches
- Don't test formatting or presentation
- Example: Don't test exact error messages, test error types

### 3. Test Duplication
- Don't repeat test logic
- Use helper functions for common setup
- Share test data appropriately
- Example: Use `create_minimal_spec()` helper

### 4. Testing Too Much
- Don't test everything
- Focus on critical paths
- Test behavior, not implementation
- Example: Test workflow compilation, not every possible node type

### 5. Ignoring Warnings
- Address deprecation warnings
- Keep up with library updates
- Update tests for API changes
- Example: Update StateGraph initialization for new LangGraph version

## Continuous Improvement

### 1. Regular Review
- Review tests with code changes
- Update tests for new features
- Remove obsolete tests
- Example: Review tests when adding new workflow types

### 2. Documentation
- Keep test documentation up to date
- Document test patterns and helpers
- Explain complex test scenarios
- Example: Document test data structures and helpers

### 3. Maintenance
- Regular test cleanup
- Update for new requirements
- Remove redundant tests
- Example: Clean up tests when refactoring code

### 4. Learning from Mistakes
- Document test failures
- Update principles based on experience
- Share lessons learned
- Example: Document issues with testing third-party libraries
