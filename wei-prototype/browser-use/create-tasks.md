# Create Task

> Create and start a new Browser Use Agent task.

This is the main endpoint for running AI agents. You can either:

1. Start a new session with a new task.
2. Add a follow-up task to an existing session.

When starting a new session:

- A new browser session is created
- Credits are deducted from your account
- The agent begins executing your task immediately

When adding to an existing session:

- The agent continues in the same browser context
- No additional browser start up costs are charged (browser session is already active)
- The agent can build on previous work

Key features:

- Agent profiles: Define agent behavior and capabilities
- Browser profiles: Control browser settings and environment (only used for new sessions)
- File uploads: Include documents for the agent to work with
- Structured output: Define the format of the task result
- Task metadata: Add custom data for tracking and organization

Args:

- request: Complete task configuration including agent settings, browser settings, and task description

Returns:

- The created task ID together with the task's session ID

Raises:

- 402: If user has insufficient credits for a new session
- 404: If referenced agent/browser profiles don't exist
- 400: If session is stopped or already has a running task

## OpenAPI

```yaml https://app.stainless.com/api/spec/documented/browser-use/openapi.documented.yml post /tasks
paths:
  path: /tasks
  method: post
  request:
    security:
      - title: APIKeyHeader
        parameters:
          query: {}
          header:
            X-Browser-Use-API-Key:
              type: apiKey
          cookie: {}
    parameters:
      path: {}
      query: {}
      header: {}
      cookie: {}
    body:
      application/json:
        schemaArray:
          - type: object
            properties:
              task:
                allOf:
                  - type: string
                    maxLength: 100000
                    minLength: 1
                    title: Task
              agentSettings:
                allOf:
                  - $ref: "#/components/schemas/AgentSettingsView"
              browserSettings:
                allOf:
                  - $ref: "#/components/schemas/BrowserSettingsView"
              structuredOutputJson:
                allOf:
                  - anyOf:
                      - type: string
                      - type: "null"
                    title: Structuredoutputjson
              includedFileNames:
                allOf:
                  - anyOf:
                      - items:
                          type: string
                        type: array
                      - type: "null"
                    title: Includedfilenames
              metadata:
                allOf:
                  - anyOf:
                      - additionalProperties:
                          type: string
                        type: object
                      - type: "null"
                    title: Metadata
              secrets:
                allOf:
                  - anyOf:
                      - additionalProperties:
                          type: string
                        type: object
                      - type: "null"
                    title: Secrets
            required: true
            title: CreateTaskRequest
            description: |-
              Request model for creating a new task

              Attributes:
                  task: The task prompt/instruction for the agent
                  agent_settings: Agent configuration (optional)
                  browser_settings: Browser configuration (optional)
                  included_file_names: Optional list of file names to include in the task (file names from user file presigned upload URL response)
                  structured_output_json: JSON schema for structured output (optional)
                  metadata: Additional metadata associated with the task (optionally set by the user)
                      secrets: Sensitive data (passwords, tokens) for the session (deleted after session is stopped)
            refIdentifier: "#/components/schemas/CreateTaskRequest"
            requiredProperties:
              - task
        examples:
          example:
            value:
              task: <string>
              agentSettings:
                llm: o3
                startUrl: <string>
                profileId: 3c90c3cc-0d44-4b50-8888-8dd25736052a
              browserSettings:
                sessionId: 3c90c3cc-0d44-4b50-8888-8dd25736052a
                profileId: 3c90c3cc-0d44-4b50-8888-8dd25736052a
              structuredOutputJson: <string>
              includedFileNames:
                - <string>
              metadata: {}
              secrets: {}
    codeSamples:
      - lang: JavaScript
        source: |-
          import BrowserUse from 'browser-use-sdk';

          const client = new BrowserUse({
            apiKey: 'My API Key',
          });

          const task = await client.tasks.create({ task: 'x' });

          console.log(task.id);
      - lang: Python
        source: |-
          from browser_use_sdk import BrowserUse

          client = BrowserUse(
              api_key="My API Key",
          )
          task = client.tasks.create(
              task="x",
          )
          print(task.id)
  response:
    "202":
      application/json:
        schemaArray:
          - type: object
            properties:
              id:
                allOf:
                  - type: string
                    format: uuid
                    title: Id
              sessionId:
                allOf:
                  - type: string
                    format: uuid
                    title: Sessionid
            title: TaskCreatedResponse
            description: |-
              Response model for creating a task

              Attributes:
                      task_id: An unique identifier for the created task
                      session_id: The ID of the session this task belongs to
            refIdentifier: "#/components/schemas/TaskCreatedResponse"
            requiredProperties:
              - id
              - sessionId
        examples:
          example:
            value:
              id: 3c90c3cc-0d44-4b50-8888-8dd25736052a
              sessionId: 3c90c3cc-0d44-4b50-8888-8dd25736052a
        description: Successful Response
    "422":
      application/json:
        schemaArray:
          - type: object
            properties:
              detail:
                allOf:
                  - items:
                      $ref: "#/components/schemas/ValidationError"
                    type: array
                    title: Detail
            title: HTTPValidationError
            refIdentifier: "#/components/schemas/HTTPValidationError"
        examples:
          example:
            value:
              detail:
                - loc:
                    - <string>
                  msg: <string>
                  type: <string>
        description: Validation Error
  deprecated: false
  type: path
components:
  schemas:
    AgentSettingsView:
      properties:
        llm:
          $ref: "#/components/schemas/SupportedLLMs"
          default: o3
        startUrl:
          anyOf:
            - type: string
            - type: "null"
          title: Starturl
        profileId:
          anyOf:
            - type: string
              format: uuid
            - type: "null"
          title: Profileid
      type: object
      title: AgentSettingsView
      description: |-
        Configuration settings for the agent

        Attributes:
            llm: The LLM model to use for the agent
                start_url: Optional URL to start the agent on (will not be changed as a step)
            profile_id: Unique identifier of the agent profile to use for the task
    BrowserSettingsView:
      properties:
        sessionId:
          anyOf:
            - type: string
              format: uuid
            - type: "null"
          title: Sessionid
        profileId:
          anyOf:
            - type: string
              format: uuid
            - type: "null"
          title: Profileid
      type: object
      title: BrowserSettingsView
      description: |-
        Configuration settings for the browser session

        Attributes:
            session_id: Unique identifier of existing session to continue
            profile_id: Unique identifier of browser profile to use (use if you want to start a new session)
    SupportedLLMs:
      type: string
      enum:
        - gpt-4.1
        - gpt-4.1-mini
        - o4-mini
        - o3
        - gemini-2.5-flash
        - gemini-2.5-pro
        - claude-sonnet-4-20250514
        - gpt-4o
        - gpt-4o-mini
        - llama-4-maverick-17b-128e-instruct
        - claude-3-7-sonnet-20250219
      title: SupportedLLMs
    ValidationError:
      properties:
        loc:
          items:
            anyOf:
              - type: string
              - type: integer
          type: array
          title: Location
        msg:
          type: string
          title: Message
        type:
          type: string
          title: Error Type
      type: object
      required:
        - loc
        - msg
        - type
      title: ValidationError
```
