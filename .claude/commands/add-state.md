Add a new conversation state to the FSM.

Ask me for:
1. State name and purpose
2. What triggers entry into this state (which previous state + what user input)
3. What message should be displayed (text, quick replies, flex, etc.)
4. What transitions out of this state (user inputs → next states)

Then:
1. Add the new `State` enum value in `app/handlers/conversation_handler.py`
2. Create the handler function
3. Register it in `_STATE_HANDLERS`
4. Add the message builder in `app/builders/conversation_messages.py`
5. Update any existing state handlers that should transition to this new state
6. Add tests
7. Run the test suite
