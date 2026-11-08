@claim:observed
Feature: probe

  @CLM-001
  Scenario: a negative value is refused
    Given a value of -1
    Then it is refused

  @CLM-003 @claim:intended
  Scenario: a refusal is reported
    Given a value of -1
    Then the report names the reason

  @claim:inferred
  Rule: what the code was read to do

    @CLM-002
    Scenario: zero is accepted
      Given a value of 0
      Then it is accepted

    @CLM-005
    Scenario: a word is refused
      Given a value of "ten"
      Then it is refused
