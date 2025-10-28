# Phase 3: Multi-Touch Sequences - Implementation Plan

## 🎯 Goal
Build a visual sequence builder and execution engine for automated, multi-step email campaigns with conditional logic and time delays.

---

## 📋 Phase 3 Breakdown

### **1. Database Schema** ⏳
**Tables to Create:**

```sql
-- sequences: Define email sequences/drip campaigns
CREATE TABLE sequences (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    user_id UUID NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT (draft/active/paused/archived),
    steps_count INTEGER,
    settings JSONB, -- default delays, timezone, send times
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- sequence_steps: Individual steps in a sequence
CREATE TABLE sequence_steps (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    sequence_id UUID NOT NULL,
    step_order INTEGER NOT NULL, -- 1, 2, 3...
    step_type TEXT, -- email, delay, condition, action
    name TEXT,
    
    -- Email content
    email_template_id UUID, -- Optional: link to template
    subject_line TEXT,
    body_text TEXT,
    body_html TEXT,
    
    -- Timing
    delay_days INTEGER DEFAULT 0,
    delay_hours INTEGER DEFAULT 0,
    send_time TEXT, -- "09:00" (optional specific time)
    
    -- Conditional logic
    condition_type TEXT, -- if_replied, if_opened, if_clicked, if_not_replied
    condition_value JSONB,
    
    -- Actions
    action_type TEXT, -- update_status, tag_lead, notify_user
    action_config JSONB,
    
    -- A/B Testing
    variant TEXT, -- A, B (for split testing)
    
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(sequence_id, step_order)
);

-- lead_sequence_state: Track where each lead is in each sequence
CREATE TABLE lead_sequence_state (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    lead_id UUID NOT NULL,
    campaign_id UUID NOT NULL,
    sequence_id UUID NOT NULL,
    
    -- Current state
    current_step_id UUID, -- Which step they're on
    current_step_order INTEGER,
    status TEXT, -- active, paused, completed, stopped
    
    -- Progress tracking
    started_at TIMESTAMP,
    next_action_at TIMESTAMP, -- When to execute next step
    completed_at TIMESTAMP,
    stopped_reason TEXT,
    
    -- Engagement tracking
    emails_sent INTEGER DEFAULT 0,
    emails_opened INTEGER DEFAULT 0,
    emails_clicked INTEGER DEFAULT 0,
    emails_replied INTEGER DEFAULT 0,
    
    -- Metadata
    metadata JSONB, -- Custom data, tags, etc.
    
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(lead_id, sequence_id)
);

-- sequence_execution_log: Audit trail of all sequence actions
CREATE TABLE sequence_execution_log (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    lead_id UUID NOT NULL,
    sequence_id UUID NOT NULL,
    step_id UUID NOT NULL,
    
    action_type TEXT, -- email_sent, delay_started, condition_evaluated, step_skipped
    action_result TEXT, -- success, failed, skipped
    error_message TEXT,
    
    -- Context
    step_order INTEGER,
    metadata JSONB,
    
    executed_at TIMESTAMP DEFAULT NOW()
);
```

**Indexes & RLS:**
- Tenant isolation on all tables
- Fast lookups by sequence_id, lead_id, next_action_at
- RLS policies for multi-tenancy

---

### **2. Backend API Endpoints** ⏳

#### **Sequence Management:**
```python
POST   /sequences                    # Create new sequence
GET    /sequences                    # List all sequences
GET    /sequences/{id}               # Get sequence details
PUT    /sequences/{id}               # Update sequence
DELETE /sequences/{id}               # Delete sequence
POST   /sequences/{id}/duplicate     # Clone sequence

# Sequence Steps
GET    /sequences/{id}/steps         # Get all steps
POST   /sequences/{id}/steps         # Add step
PUT    /sequences/{id}/steps/{step}  # Update step
DELETE /sequences/{id}/steps/{step}  # Delete step
POST   /sequences/{id}/steps/reorder # Reorder steps
```

#### **Sequence Assignment:**
```python
POST   /campaigns/{id}/assign-sequence  # Assign sequence to campaign
GET    /campaigns/{id}/sequences        # Get campaign sequences
DELETE /campaigns/{id}/sequences/{seq}  # Remove sequence from campaign
```

#### **Sequence Execution:**
```python
POST   /sequences/{id}/start           # Start/activate sequence
POST   /sequences/{id}/pause            # Pause sequence
POST   /sequences/{id}/resume           # Resume sequence
GET    /sequences/{id}/progress         # Get execution progress
GET    /sequences/{id}/analytics        # Sequence performance

# Lead-level control
POST   /leads/{id}/assign-sequence      # Add lead to sequence
POST   /leads/{id}/pause-sequence       # Pause lead's sequence
POST   /leads/{id}/resume-sequence      # Resume lead's sequence
POST   /leads/{id}/skip-step            # Skip current step
GET    /leads/{id}/sequence-state       # Get lead's sequence state
```

#### **Background Job Scheduler:**
```python
# Cron job endpoint (runs every 5 minutes)
POST   /sequences/process-queue         # Process pending sequence actions
GET    /sequences/queue-status          # Check queue health
```

---

### **3. Sequence Execution Engine** ⏳

**Core Logic:**

```python
class SequenceEngine:
    async def process_queue(self):
        """Main scheduler - runs every 5 minutes"""
        # Get all leads with next_action_at <= NOW
        pending_actions = await self.get_pending_actions()
        
        for action in pending_actions:
            await self.execute_step(action)
    
    async def execute_step(self, lead_sequence_state):
        """Execute the next step for a lead"""
        step = await self.get_current_step(lead_sequence_state)
        
        if step.step_type == 'email':
            await self.send_email(lead_sequence_state, step)
        
        elif step.step_type == 'delay':
            await self.schedule_delay(lead_sequence_state, step)
        
        elif step.step_type == 'condition':
            await self.evaluate_condition(lead_sequence_state, step)
        
        elif step.step_type == 'action':
            await self.execute_action(lead_sequence_state, step)
        
        # Move to next step
        await self.advance_to_next_step(lead_sequence_state)
    
    async def evaluate_condition(self, state, step):
        """Conditional branching logic"""
        if step.condition_type == 'if_replied':
            # Check if lead replied in last X days
            if await self.has_replied(state.lead_id):
                # Mark as qualified, stop sequence
                await self.complete_sequence(state, 'replied')
            else:
                # Continue to next step
                pass
        
        elif step.condition_type == 'if_opened':
            # Check if email was opened
            if await self.has_opened(state.lead_id, step):
                # Continue to "interested" path
                pass
            else:
                # Skip to "not interested" path
                await self.skip_to_step(state, step.condition_value['skip_to'])
    
    async def schedule_delay(self, state, step):
        """Calculate when to execute next step"""
        delay = timedelta(
            days=step.delay_days,
            hours=step.delay_hours
        )
        
        # Consider send time preferences (e.g., only send 9am-5pm)
        next_action_at = self.calculate_next_send_time(
            datetime.now() + delay,
            step.send_time,
            state.timezone
        )
        
        await self.update_next_action(state, next_action_at)
```

**Features:**
- Timezone-aware scheduling
- Smart send times (9am-5pm, business days only)
- Conditional branching based on engagement
- Auto-stop on reply/unsubscribe
- A/B testing support

---

### **4. Frontend Sequence Builder** ⏳

**New Pages:**

```
/sequences                  # List all sequences
/sequences/new              # Create new sequence
/sequences/{id}/edit        # Visual sequence builder
```

**Visual Builder Components:**

```javascript
// Drag-and-drop sequence builder
<SequenceBuilder>
  <StepPalette>          // Drag steps from here
    - Email Step
    - Delay Step
    - Condition Step
    - Action Step
  </StepPalette>
  
  <Canvas>               // Drop steps here
    <SequenceStep type="email" order={1}>
      <EmailEditor />
    </SequenceStep>
    
    <SequenceStep type="delay" order={2}>
      <DelayPicker />
    </SequenceStep>
    
    <SequenceStep type="condition" order={3}>
      <ConditionBuilder />
    </SequenceStep>
  </Canvas>
  
  <StepProperties>       // Edit selected step
    <EmailContent />
    <DelaySettings />
    <ConditionLogic />
  </StepProperties>
</SequenceBuilder>
```

**UI Features:**
- Drag-and-drop step creation
- Visual flow diagram
- Step reordering
- Email template editor with variables
- Delay picker (days/hours)
- Conditional logic builder
- Preview mode
- Duplicate sequence
- Import/export sequences

---

### **5. Campaign Integration** ⏳

**Assign Sequence to Campaign:**
- When campaign is created, optionally assign a sequence
- All leads in campaign automatically enter sequence
- Track sequence performance per campaign

**Lead Assignment:**
- Manual: Add individual leads to sequence
- Automatic: All new campaign leads → sequence
- Conditional: If lead matches criteria → sequence

---

### **6. Email Templates** ⏳

**Template Variables:**
```
{{lead.name}}
{{lead.company}}
{{lead.title}}
{{user.name}}
{{user.email}}
{{campaign.name}}
{{custom.field_name}}
```

**Template Library:**
- Pre-built templates (cold outreach, follow-up, re-engagement)
- Custom templates
- A/B test variants
- Rich text editor

---

## 📦 Implementation Order

### **Step 1: Database (Day 1)** ⏳
- Create `phase3_sequences_schema.sql`
- Run migration in Supabase
- Test table creation

### **Step 2: Backend API - Sequence CRUD (Day 1-2)** ⏳
- Sequence management endpoints
- Step management endpoints
- Basic validation

### **Step 3: Sequence Assignment (Day 2)** ⏳
- Assign sequence to campaign
- Add leads to sequence
- Lead sequence state tracking

### **Step 4: Execution Engine Core (Day 2-3)** ⏳
- Email step execution
- Delay scheduling
- Background job processor
- Integration with email service

### **Step 5: Conditional Logic (Day 3)** ⏳
- Condition evaluation
- Branching logic
- Auto-stop on reply

### **Step 6: Frontend - Sequence List (Day 3-4)** ⏳
- List sequences page
- Create/edit basic sequence form
- Assign to campaign

### **Step 7: Visual Builder (Day 4-5)** ⏳
- Drag-and-drop canvas
- Step palette
- Step editor
- Flow visualization

### **Step 8: Testing & Polish (Day 5)** ⏳
- End-to-end sequence testing
- Edge case handling
- UI/UX refinement

---

## 🎯 Success Metrics

**Functionality:**
- ✅ Create multi-step sequences
- ✅ Assign sequences to campaigns
- ✅ Automated email sending with delays
- ✅ Conditional branching based on engagement
- ✅ Lead-level sequence control
- ✅ Progress tracking per lead
- ✅ Performance analytics per sequence

**UX:**
- ✅ Intuitive visual builder
- ✅ Easy step creation
- ✅ Clear sequence flow
- ✅ Real-time preview

---

## 🚧 Technical Challenges

1. **Scheduler Reliability:**
   - Need robust background job system
   - Handle failures gracefully
   - Avoid duplicate sends

2. **Timezone Handling:**
   - Send at recipient's local time
   - Respect business hours

3. **Conditional Logic:**
   - Complex branching paths
   - Circular dependency detection

4. **Performance:**
   - Process 1000s of leads efficiently
   - Batch email sending
   - Queue optimization

---

## 🔮 Future Enhancements (Post-Phase 3)

- Visual flowchart editor (like Zapier)
- Advanced A/B testing
- Smart send time optimization (AI-powered)
- SMS/LinkedIn steps
- Goal tracking (meetings booked, deals closed)
- Sequence templates marketplace

---

## 📊 Estimated Effort

- **Database Schema:** 2 hours
- **Backend API:** 8 hours
- **Execution Engine:** 12 hours
- **Frontend Builder:** 16 hours
- **Testing & Polish:** 6 hours

**Total: ~44 hours (5-6 days)**

---

**Ready to start with Step 1: Database Schema?** 🚀

