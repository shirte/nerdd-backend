Feature: Jobs
    Background:
        Given a mocked channel
        And a mocked repository
        And the repository contains the mol weight module

    Scenario: Uploading a valid job
        When the client sends a POST request to /jobs/ with content
            {
                "job_type": "mol_scale",
                "source_id": "1",
                "params": { "multiplier": 10 }
            }

    Scenario: Get non-existing job
        When the client requests /jobs/1
        Then the status code of the response is 404