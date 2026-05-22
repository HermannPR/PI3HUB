
## Phone UI — interaction style

**You are controlled from a phone wrapper that reads this terminal.**
The phone app parses your output and renders interactive buttons automatically.

### Rules (follow every response)

1. **Always end with numbered options** when the user needs to choose or continue:
   ```
   > 1. option one
     2. option two
     3. option three
   ```
   The phone renders these as tap buttons automatically.

2. **Use [y/n] format** for simple confirmations — the phone shows YES/NO buttons:
   ```
   Do something risky? [y/n]
   ```

3. **Keep options short** — labels truncate at ~28 chars in the phone UI.

4. **Keep prose short** — phone preview shows ~20 lines. Lead with key info, skip filler.

5. **After completing any task**, always offer next steps as numbered options. Never end with no choices.

6. **When proposing a plan**, number the steps AND ask which to do:
   ```
   Plan: X, Y, Z.
   > 1. Do it
     2. Modify plan
     3. Cancel
   ```

7. **Typical option sets:**
   - After task: `1. Continue  2. Test it  3. Next task  4. Done`
   - Confirmation: `[y/n]`
   - On error: `1. Fix it  2. Skip  3. Show details`
   - Idle: `1. What's next?  2. Pi status  3. Ideas`

### What NOT to do
- Don't end a response with just prose and no options
- Don't give more than 5 options (phone screen fits ~4 wide)
- Don't use long sentences in option labels
