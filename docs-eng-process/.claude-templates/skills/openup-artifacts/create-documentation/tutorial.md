# Tutorial Documentation

This file provides detailed instructions for creating tutorials that guide users through learning a feature or system.

## When to Create Tutorials

Create tutorials when:
- Onboarding new users or developers
- Teaching complex workflows
- Demonstrating best practices
- Providing hands-on learning experiences
- Supporting different learning styles

## Tutorial Types

**Getting Started Tutorials:**
- First-time user experience
- Installation and setup
- Hello World examples

**Feature Tutorials:**
- Deep dive into specific features
- Real-world use cases
- Step-by-step workflows

**Advanced Tutorials:**
- Complex integrations
- Performance optimization
- Customization and extensions

## Process

### 1. Define Learning Objectives

What should the learner be able to do after completing the tutorial?

Use SMART objectives:
- Specific: Clear, focused outcome
- Measurable: Can verify it's done
- Achievable: Realistic for the timeframe
- Relevant: Aligned with user goals
- Time-bound: Completable in one sitting

Example:
"After this tutorial, you will be able to create a user account, log in, and update your profile settings."

### 2. Identify Prerequisites

What does the learner need before starting?

**Knowledge Prerequisites:**
- Programming languages
- Concepts (e.g., "understands REST APIs")
- Previous tutorials to complete

**Tool Prerequisites:**
- Software to install
- Accounts to create
- Access permissions needed

**Time Requirement:**
- Estimated completion time
- Suggested session breakdown

### 3. Structure the Tutorial

**Progressive Disclosure:**
- Start simple, add complexity gradually
- One concept at a time
- Build on previous steps

**Example Structure:**

1. **Overview**
   - What you'll build
   - Why it matters
   - How long it will take

2. **Prerequisites**
   - What you need before starting
   - Setup instructions

3. **Step-by-Step Instructions**
   - Numbered steps
   - Code examples
   - Explanations for each step
   - Expected results

4. **Verification**
   - How to check it works
   - What success looks like

5. **Next Steps**
   - What to learn next
   - Related tutorials
   - Advanced topics

6. **Troubleshooting**
   - Common issues
   - How to get help

### 4. Write Clear Instructions

**Guidelines:**

- Use imperative mood ("Do this" not "You should do this")
- One action per step
- Show, then explain
- Provide context for why

**Example:**

Good:
```
1. Create a new file named `app.js` in your project directory.
2. Add the following code to import the required modules:

   ```javascript
   const express = require('express');
   const app = express();
   ```

   This code imports Express and creates an application instance.
```

Poor:
```
You should create a file for your code and then you need to import the modules
that you're going to use which would be Express...
```

### 5. Provide Working Examples

Every code example should:
- Be complete and runnable
- Use realistic but simple data
- Include comments for key lines
- Show expected output

**Example Format:**

```javascript
// Create a new user
const user = {
  name: 'Jane Doe',
  email: 'jane@example.com'
};

// Send to API
const response = await fetch('/api/users', {
  method: 'POST',
  body: JSON.stringify(user)
});

// Expected response: { id: 123, name: 'Jane Doe', email: 'jane@example.com' }
```

### 6. Add Checkpoints

After major sections, add checkpoints:
- "You should now have..."
- "Verify that..."
- "If you see X, you're on the right track"

Checkpoint example:
```
**Checkpoint:** At this point, your project structure should look like this:

my-project/
├── app.js
├── package.json
└── README.md

If your structure looks different, review the previous steps.
```

### 7. Include Visual Aids

Where appropriate, add:
- Screenshots (with annotations)
- Diagrams showing architecture or flow
- Code highlighting
- Progress indicators

### 8. Test the Tutorial

Before publishing:
- Follow your own instructions exactly
- Have someone unfamiliar test it
- Time how long it takes
- Note where people get stuck

### 9. Provide Next Steps

At the end, guide learners to:
- Related tutorials
- Advanced topics
- Real-world applications
- Community resources

## Tutorial Length Guidelines

| Type | Target Length | Session Time |
|------|---------------|--------------|
| Quick Start | 5-10 steps | 15-30 minutes |
| Feature Tutorial | 10-20 steps | 30-60 minutes |
| Advanced Tutorial | 20+ steps | 60-90 minutes |

## Common Pitfalls

| Pitfall | Solution |
|---------|----------|
| Too long | Break into multiple tutorials |
| Assumes too much | Add prerequisite checks |
| No verification | Add checkpoints and tests |
| Boring examples | Use realistic scenarios |
| Missing context | Explain why, not just how |
| Dead ends | Provide next steps |
