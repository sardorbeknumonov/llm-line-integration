Simulate the full Margaret ordering flow by tracing through the conversation handler.

Read `app/handlers/conversation_handler.py` and `app/builders/conversation_messages.py`, then walk through the complete flow step by step:

1. User sends "Hello"
2. User taps "🍜 Noodles"
3. User taps "Uncle Sam's Noodle House"
4. User taps "Classic Pork Noodle Soup (Large)"
5. User taps "No, I'm good!"
6. User taps "✅ Confirm Order"
7. User taps "💚 LINE Pay"
8. (delivery tracking pushes)
9. User taps "⭐⭐⭐⭐⭐"
10. User taps "😋 Delicious!"

For each step, show:
- Current state → Next state
- What LINE message type is sent (text, flex carousel, flex bubble, quick reply)
- Key content in the message

This validates the flow works end-to-end without needing to deploy.
