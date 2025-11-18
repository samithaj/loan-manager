# Bike Lifecycle Management System - Training Guide

**For Trainers and New Users**
**Version**: 1.0.0
**Last Updated**: November 2025

---

## Table of Contents

1. [Training Overview](#training-overview)
2. [Training Schedules](#training-schedules)
3. [Module 1: System Introduction](#module-1-system-introduction)
4. [Module 2: Basic Operations](#module-2-basic-operations)
5. [Module 3: Advanced Features](#module-3-advanced-features)
6. [Module 4: Reporting & Analytics](#module-4-reporting--analytics)
7. [Hands-On Exercises](#hands-on-exercises)
8. [Assessment & Certification](#assessment--certification)
9. [Train-the-Trainer Guide](#train-the-trainer-guide)
10. [Quick Reference Cards](#quick-reference-cards)

---

## Training Overview

### Purpose

This training program ensures all users can effectively use the Bike Lifecycle Management System to:
- Manage bike inventory efficiently
- Track costs accurately
- Process sales correctly
- Generate meaningful reports
- Follow standard operating procedures

### Training Objectives

By the end of training, participants will be able to:
- ✅ Navigate the system confidently
- ✅ Record bike acquisitions with complete information
- ✅ Process sales transactions accurately
- ✅ Track repairs and maintenance costs
- ✅ Initiate and manage transfers
- ✅ Generate and interpret reports
- ✅ Troubleshoot common issues

### Who Needs Training?

| Role | Training Required | Duration |
|------|-------------------|----------|
| Branch Managers | Full Training | 4 hours |
| Sales Staff | Core Training | 3 hours |
| Mechanics | Repair Module | 1.5 hours |
| Finance Team | Reports Module | 2 hours |
| Administrators | Advanced Training | 6 hours |

### Training Delivery Methods

**In-Person Training**
- Instructor-led sessions
- Hands-on practice with test environment
- Group exercises
- Q&A sessions

**Online Training**
- Video tutorials
- Self-paced learning modules
- Virtual workshops
- Webinar series

**On-the-Job Training**
- Shadowing experienced users
- Supervised practice
- Gradual responsibility increase

---

## Training Schedules

### Branch Manager Training (4 Hours)

**Day 1: Core Operations (4 hours)**

| Time | Topic | Duration |
|------|-------|----------|
| 9:00 - 9:30 | System Introduction & Login | 30 min |
| 9:30 - 10:30 | Bike Acquisition Process | 60 min |
| 10:30 - 10:45 | *Break* | 15 min |
| 10:45 - 11:45 | Inventory Management & Searching | 60 min |
| 11:45 - 12:30 | Recording Sales | 45 min |
| 12:30 - 1:00 | Transfer Management | 30 min |

**Materials Needed**:
- Training login credentials
- Sample bike data
- Printed quick reference guide

### Sales Staff Training (3 Hours)

| Time | Topic | Duration |
|------|-------|----------|
| 2:00 - 2:30 | System Navigation & Dashboard | 30 min |
| 2:30 - 3:15 | Searching & Viewing Inventory | 45 min |
| 3:15 - 3:30 | *Break* | 15 min |
| 3:30 - 4:30 | Recording Sales (Detailed) | 60 min |
| 4:30 - 5:00 | Practice Exercises | 30 min |

### Mechanic Training (1.5 Hours)

| Time | Topic | Duration |
|------|-------|----------|
| 10:00 - 10:15 | Login & Navigation | 15 min |
| 10:15 - 11:00 | Adding Repair Jobs | 45 min |
| 11:00 - 11:30 | Practice & Q&A | 30 min |

### Finance Team Training (2 Hours)

| Time | Topic | Duration |
|------|-------|----------|
| 2:00 - 2:30 | System Overview | 30 min |
| 2:30 - 3:30 | Reports & Analytics | 60 min |
| 3:30 - 4:00 | Data Export & Analysis | 30 min |

---

## Module 1: System Introduction

**Duration**: 30 minutes
**Audience**: All users

### Learning Objectives

- Understand system purpose and benefits
- Successfully log in and log out
- Navigate the main menu and dashboard
- Identify key UI elements

### Lesson Plan

#### Introduction (5 minutes)

**Trainer Says**:
> "Welcome to the Bike Lifecycle Management System training. This system will help us manage our entire bike sales operation more efficiently. Today, we'll learn how to use this system to make your job easier and more accurate."

**Key Points**:
- System manages complete bike lifecycle
- Reduces paperwork and errors
- Provides real-time visibility
- Improves decision making

#### System Access (10 minutes)

**Demo**: Logging In
1. Open browser and navigate to system URL
2. Enter username and password
3. Click "Sign In"
4. Show dashboard appears

**Hands-On**: Each participant logs in
- Provide individual credentials
- Verify everyone successfully logged in
- Troubleshoot any issues

**Security Reminders**:
- Never share your password
- Log out when leaving computer
- Password should be changed regularly

#### Dashboard Tour (10 minutes)

**Walk through each section**:

1. **Top Navigation Bar**
   - Logo and home button
   - Main menu (Bikes, Reports, Admin)
   - User profile icon
   - Notification bell

2. **Dashboard Widgets**
   - Total Bikes card
   - Active Transfers
   - This Month's Sales
   - Pending Actions

3. **Quick Actions**
   - "+ Add New Bike"
   - "View Inventory"
   - "Create Transfer"
   - "Record Sale"

**Activity**: Navigation Scavenger Hunt
- "Click on Reports menu - what options do you see?"
- "Find your username - where is it displayed?"
- "How many bikes are in stock?" (read from dashboard)

#### Q&A (5 minutes)

Common questions:
- "Can I access this from my phone?" (Yes)
- "What browser should I use?" (Chrome, Firefox, Safari, Edge)
- "Who do I contact if I can't log in?" (Branch manager or IT support)

### Training Materials

- [ ] Login credentials sheet
- [ ] Dashboard screenshot handout
- [ ] Navigation quick reference card

---

## Module 2: Basic Operations

**Duration**: 2 hours
**Audience**: Branch managers, sales staff

### Section 2.1: Adding a New Bike (45 minutes)

#### Learning Objectives
- Complete bike acquisition form
- Understand required vs optional fields
- Recognize auto-generated stock numbers
- Verify bike appears in inventory

#### Lesson Plan

**Introduction (5 minutes)**

**Trainer Says**:
> "The first step in our process is acquiring a bike. When we purchase a bike, we need to record all its details in the system. This creates a permanent record and assigns a unique stock number."

**Demo: Complete Acquisition Flow (15 minutes)**

**Live demonstration**:
1. Navigate to Bikes > Acquisition
2. Fill in form with sample bike:
   ```
   Company: MA
   Branch: WW
   Title: Honda CB 125F 2020
   Brand: Honda
   Model: CB 125F
   Year: 2020
   Purchase Price: 150,000
   License Plate: ABC-1234
   Supplier: Test Supplier
   Procured By: John Doe
   ```
3. Submit and show success screen
4. Note the auto-generated stock number (e.g., MA/WW/ST/2066)
5. Navigate to inventory and find the newly added bike

**Key Teaching Points**:
- **Required fields** marked with red asterisk (*)
- **Stock number** is automatic - don't try to enter it
- **Purchase price** is critical for P/L calculation
- **License plate** should be unique - system warns if duplicate
- **Procurement date** defaults to today

**Hands-On Exercise (20 minutes)**

**Instructions**: "Now it's your turn. Add a bike with these details:"

```
Company: [Your Company]
Branch: [Your Branch]
Title: Yamaha FZ 2019
Brand: Yamaha
Model: FZ
Year: 2019
Condition: USED
Purchase Price: 140,000
License Plate: XYZ-5678
Supplier Name: Lanka Motors
Supplier Contact: 0771234567
Procured By: [Your Name]
Payment Method: CASH
```

**Trainer walks around**:
- Check each participant's screen
- Answer questions
- Ensure everyone completes successfully
- Verify stock numbers were assigned

**Common Mistakes to Address**:
- Forgetting to select branch
- Typing text in price field (use numbers only)
- Not saving before closing
- Entering past dates incorrectly

**Review (5 minutes)**

**Ask participants**:
1. "What happens if you leave a required field empty?" (Can't submit)
2. "Can you change the stock number?" (No, automatic)
3. "Where do you find the bike after adding it?" (Inventory)

### Section 2.2: Searching and Viewing Inventory (30 minutes)

#### Learning Objectives
- Use filters to find bikes
- Search by stock number and license plate
- View bike details
- Understand bike status meanings

#### Lesson Plan

**Introduction (5 minutes)**

**Trainer Says**:
> "With hundreds of bikes in the system, we need efficient ways to find what we're looking for. The inventory page has powerful filters and search capabilities."

**Demo: Filtering and Searching (10 minutes)**

**Show each filter**:

1. **Company Filter**
   - Select "MA" - show results update
   - Select "All" - show all companies

2. **Branch Filter**
   - Select "WW" - show only Walasmulla bikes
   - Explain: "You only see branches you have access to"

3. **Status Filter**
   - Select "IN_STOCK" - explain these are available for sale
   - Select "SOLD" - explain these are historical records
   - Go through each status:
     - IN_STOCK: Ready to sell
     - SOLD: Already sold
     - IN_TRANSIT: Being transferred
     - ALLOCATED: Reserved/being transferred
     - MAINTENANCE: Under repair

4. **Search Box**
   - Type a stock number (e.g., "MA/WW/ST/2066")
   - Type a license plate (e.g., "ABC-1234")
   - Show instant results

**Demo: Viewing Bike Details (10 minutes)**

Click on a bike card to show:
- **Overview tab**: All bike information
- **Cost Summary tab**: Financial breakdown
- **Stock History tab**: Event timeline
- **Transfers tab**: Transfer records

**Hands-On Exercise (10 minutes)**

**Tasks for participants**:
1. "Filter to show only IN_STOCK bikes in your branch"
2. "Find the bike you just added using search"
3. "Click on any bike and review its details"
4. "Find a sold bike and check its profit/loss"

**Review (5 minutes)**

Quiz questions:
1. "How do you clear all filters?" (Click "Clear Filters" or select "All")
2. "What does IN_TRANSIT status mean?" (Being transferred)
3. "Where do you see a bike's purchase price?" (Detail page or inventory card)

### Section 2.3: Recording a Sale (45 minutes)

#### Learning Objectives
- Complete sales form accurately
- Understand P/L calculation
- Record customer information
- Verify commission calculation

#### Lesson Plan

**Introduction (5 minutes)**

**Trainer Says**:
> "Recording a sale is one of our most important tasks. It marks the successful end of a bike's journey through our system and determines our profit or loss."

**Demo: Complete Sales Process (20 minutes)**

**Step-by-step demonstration**:

1. **Find a Bike**
   - Filter for IN_STOCK bikes
   - Select one bike
   - Click "Sell" button

2. **Fill Sale Information**
   ```
   Selling Price: 195,000
   Sale Date: [Today]
   Customer Name: Saman Perera
   Customer Contact: 0771234567
   Customer NIC: 912345678V
   Customer Address: 123, Main St, Colombo
   Payment Method: CASH
   ```

3. **Review P/L Preview**
   - Show the automatic calculation
   - Explain each component:
     ```
     Purchase Price: 150,000
     + Repair Costs: 15,000
     + Branch Expenses: 5,000
     = Total Cost: 170,000

     Selling Price: 195,000
     - Total Cost: 170,000
     = Profit: 25,000 ✓
     ```
   - Point out green color = profit, red = loss

4. **Submit Sale**
   - Click "Submit Sale"
   - Show success message
   - Navigate to sales page to verify

**Important Points to Emphasize**:
- ⚠️ **Check P/L before submitting** - Don't sell at a loss without approval
- ✅ **Customer information is required** - For legal and follow-up
- 📱 **Verify contact number** - For post-sale communication
- 💰 **Payment method matters** - For accounting

**Hands-On Exercise (15 minutes)**

**Instructions**: "Record a sale with these details:"

```
Bike: [The one you added earlier - Yamaha FZ]
Selling Price: 175,000
Customer Name: Nimal Silva
Customer Contact: 0779876543
Customer NIC: 851234567V
Customer Address: 456, Lake Road, Kandy
Payment Method: BANK
```

**Check participants**:
- Verify they found the right bike
- Ensure all required fields filled
- Check they reviewed P/L
- Confirm successful submission

**Common Issues**:
- "I can't find the Sell button" - Check bike status, must be IN_STOCK
- "It says I don't have permission" - Check branch assignment
- "P/L shows a loss" - Verify selling price is higher than total cost

**Review (5 minutes)**

**Discussion questions**:
1. "What happens to bike status after sale?" (Changes to SOLD)
2. "Can you sell a bike that's IN_TRANSIT?" (No, must be IN_STOCK)
3. "How is commission calculated?" (% of profit, shown on sale screen)

### Training Materials

- [ ] Sample bike data sheet
- [ ] Practice exercise worksheets
- [ ] Status meanings reference card
- [ ] P/L calculation example handout

---

## Module 3: Advanced Features

**Duration**: 2 hours
**Audience**: Branch managers, administrators

### Section 3.1: Transfer Management (45 minutes)

#### Learning Objectives
- Initiate transfer requests
- Approve/reject transfers
- Track transfer progress
- Mark deliveries complete

#### Lesson Plan

**Introduction (5 minutes)**

**Trainer Says**:
> "Transfers allow us to move bikes between branches. This is crucial for balancing inventory and meeting customer demand across locations."

**Demo: Transfer Workflow (20 minutes)**

**Show complete workflow**:

1. **Create Transfer Request**
   - Find IN_STOCK bike
   - Click "Transfer" button
   - Fill form:
     ```
     Destination Branch: HP (Haputale)
     Reason: STOCK_REBALANCING
     Notes: Moving slow-moving stock to high-demand location
     ```
   - Submit request
   - Show bike status changes to ALLOCATED

2. **Approve Transfer** (switch to manager view)
   - Go to Bikes > Transfers
   - Click "Pending" tab
   - Review transfer details
   - Click "Approve"
   - Add approval notes: "Approved - needed at HP branch"
   - Show bike status changes to IN_TRANSIT

3. **Mark as Delivered** (switch to destination branch view)
   - Go to Transfers > In Transit tab
   - Click "Mark as Delivered"
   - Enter delivery date
   - Add notes: "Bike received in good condition"
   - Show bike status changes to IN_STOCK
   - Verify current branch updated to HP

**Transfer States Diagram**:
```
REQUEST → PENDING → APPROVED → IN_TRANSIT → DELIVERED → COMPLETED
   ↓
REJECTED/CANCELLED
```

**Hands-On Exercise (15 minutes)**

**Pair Exercise**:
- Participant A: Create transfer request
- Participant B: Approve transfer
- Participant B: Mark as delivered
- Switch roles and repeat

**Scenarios to practice**:
1. Transfer for stock rebalancing
2. Transfer for customer request
3. Transfer rejection (insufficient reason)

**Review (5 minutes)**

**Q&A**:
1. "Can you transfer a SOLD bike?" (No)
2. "Who can approve transfers?" (Branch managers, admins)
3. "Can you cancel after approval?" (Only admin, with justification)

### Section 3.2: Repair Cost Tracking (30 minutes)

#### Learning Objectives
- Add repair jobs to bikes
- Track parts and labor costs
- Understand impact on P/L
- View repair history

#### Lesson Plan

**Demo: Adding Repair Job (15 minutes)**

1. Navigate to bike detail page
2. Click "Cost Summary" tab
3. Click "Add Repair Job"
4. Fill form:
   ```
   Job Type: REPAIR
   Description: Engine oil change, brake pad replacement
   Parts Cost: 3,500
   Labor Cost: 2,000
   Mechanic: Saman (Mechanic)
   Job Date: [Today]
   Job Status: COMPLETED
   ```
5. Submit and show:
   - Total repair cost updated
   - New total cost calculated
   - P/L impact if bike later sold

**Key Teaching Points**:
- Repair costs directly affect profitability
- Add costs before selling to get accurate P/L
- Status COMPLETED applies cost, CANCELLED doesn't

**Hands-On Exercise (10 minutes)**

Add repair job to a bike:
```
Job Type: ROUTINE_MAINTENANCE
Description: Chain cleaning and lubrication
Parts Cost: 500
Labor Cost: 1,000
```

**Review (5 minutes)**

### Section 3.3: Commission System (30 minutes)

**Only for sales staff and managers**

#### Understanding Commissions

**How it works**:
1. Sale is recorded
2. System calculates profit
3. If profit > 0, commission = profit × rate%
4. Commission credited to seller

**Viewing Your Commissions**:
- Navigate to Reports > My Commissions
- See pending and paid amounts
- View details per sale

**Practice**: Calculate commission manually, then verify in system

### Training Materials

- [ ] Transfer workflow diagram
- [ ] Repair job types reference
- [ ] Commission calculation examples

---

## Module 4: Reporting & Analytics

**Duration**: 1.5 hours
**Audience**: Managers, finance team, administrators

### Section 4.1: Available Reports (30 minutes)

#### Report Types Overview

**1. Acquisition Ledger**
- Shows all bikes purchased in date range
- Use for: Tracking procurement patterns
- Key metrics: Total investment, bikes acquired

**2. Cost Summary**
- Detailed cost breakdown and P/L
- Use for: Profitability analysis
- Key metrics: Profit margin, average profit per bike

**3. Sales Report**
- All sales with revenue
- Use for: Sales performance tracking
- Key metrics: Total revenue, sales count

**4. Branch Stock Summary**
- Current inventory per branch
- Use for: Inventory management
- Key metrics: Stock levels, stock value

**5. Commission Report**
- Sales commissions by staff
- Use for: Commission payment processing
- Key metrics: Total commissions owed

#### Demo: Generating Reports (20 minutes)

**Show how to**:
1. Select report type
2. Set date range
3. Apply filters
4. Generate report
5. Export to Excel
6. Export to PDF

**Hands-On Exercise (10 minutes)**

"Generate a sales report for last month and export to Excel"

### Section 4.2: Interpreting Reports (30 minutes)

#### Key Metrics Explained

**Profit Margin %**:
```
Profit Margin = (Total Profit / Total Revenue) × 100
```

**Average Days in Stock**:
How long bikes sit before selling

**Inventory Turnover**:
How quickly stock moves

**Cost Analysis**:
- Purchase cost as % of total
- Repair cost as % of total
- Branch expenses as % of total

#### Hands-On: Report Analysis

Provide sample report, ask participants to:
1. Identify most profitable bike
2. Calculate average profit
3. Find slowest-moving inventory
4. Determine top-performing branch

### Section 4.3: Data-Driven Decision Making (30 minutes)

#### Using Reports for Business Decisions

**Scenario 1: High Repair Costs**
- Report shows repair costs eating into profit
- Decision: More selective procurement, better initial inspection

**Scenario 2: Slow-Moving Inventory**
- Branch stock report shows bikes sitting > 60 days
- Decision: Transfer to higher-demand branch, adjust pricing

**Scenario 3: Sales Performance**
- Commission report shows uneven performance
- Decision: Additional training for lower performers

**Group Exercise**: Analyze provided reports and propose action items

### Training Materials

- [ ] Sample reports (all types)
- [ ] Report interpretation guide
- [ ] Business metrics glossary

---

## Hands-On Exercises

### Exercise 1: Complete Bike Lifecycle

**Objective**: Experience full bike journey from acquisition to sale

**Steps**:
1. Add new bike (procurement)
2. Add a repair job
3. Initiate transfer to another branch
4. Approve transfer
5. Mark as delivered
6. Record sale
7. View commission earned
8. Generate sales report

**Time**: 30 minutes

**Success Criteria**:
- ✅ Bike successfully added
- ✅ Stock number assigned
- ✅ Repair costs recorded
- ✅ Transfer completed
- ✅ Sale recorded with profit
- ✅ Commission calculated

### Exercise 2: Inventory Management

**Objective**: Practice finding and organizing inventory

**Tasks**:
1. Find all bikes older than 2020 in your branch
2. Identify bikes with repair costs > LKR 20,000
3. List all bikes IN_TRANSIT
4. Find bikes sold this month
5. Calculate total value of IN_STOCK inventory

**Time**: 20 minutes

### Exercise 3: Report Generation

**Objective**: Generate and analyze business reports

**Tasks**:
1. Generate acquisition ledger for last quarter
2. Export cost summary to Excel
3. Create sales report filtered by your branch
4. Generate commission report for last month
5. Identify your top 3 most profitable sales

**Time**: 25 minutes

### Exercise 4: Problem Solving

**Objective**: Troubleshoot common issues

**Scenarios**:

**Scenario 1**: Customer calls saying they want to buy a bike they saw online, but you can't find it in inventory
- Solution path: Check filters, search by stock number, verify status

**Scenario 2**: Transfer has been pending for 3 days without approval
- Solution path: Check approver, send reminder, review transfer details

**Scenario 3**: Sale shows a loss, but manager says it should be profitable
- Solution path: Review all costs, check if repair jobs are missing, verify purchase price

**Time**: 20 minutes

---

## Assessment & Certification

### Knowledge Assessment

**Written Test (30 minutes)**

**Multiple Choice (20 questions)**

Example questions:
1. What is the format of a stock number?
   a) ST/MA/WW/2066
   b) MA/WW/ST/2066 ✓
   c) 2066/ST/MA/WW
   d) WW-MA-2066

2. Which bike status allows you to record a sale?
   a) IN_TRANSIT
   b) ALLOCATED
   c) IN_STOCK ✓
   d) MAINTENANCE

3. Commission is calculated based on:
   a) Selling price
   b) Purchase price
   c) Profit ✓
   d) Total cost

**True/False (10 questions)**

1. You can manually set a stock number. (False)
2. Repair costs affect profit/loss calculation. (True)
3. Only administrators can approve transfers. (False)

**Short Answer (5 questions)**

1. List the 4 required fields when adding a new bike.
2. Explain the transfer workflow in your own words.
3. What does P/L mean and how is it calculated?

### Practical Assessment (45 minutes)

**Hands-On Tasks**:

**Task 1**: Add a bike with provided details (10 min)
**Task 2**: Find and view specific bike using filters (5 min)
**Task 3**: Create transfer request (10 min)
**Task 4**: Record a sale with P/L calculation (15 min)
**Task 5**: Generate a report (5 min)

**Scoring**: 80% or higher to pass

### Certification

**Certificate Awarded For**:
- Completing all training modules
- Passing knowledge assessment (80%+)
- Passing practical assessment (80%+)

**Certificate Template**:
```
CERTIFICATE OF COMPLETION

This certifies that [NAME] has successfully completed the
Bike Lifecycle Management System Training Program

and is authorized to use the system in the role of [ROLE]

Date: [DATE]
Instructor: [TRAINER NAME]
Score: [SCORE]%
```

### Refresher Training

**When Needed**:
- After major system updates
- When changing roles
- If inactive for 6+ months
- Upon request

**Format**: Abbreviated 1-2 hour session focusing on updates

---

## Train-the-Trainer Guide

### For Training Coordinators

#### Preparation Checklist

**2 Weeks Before**:
- [ ] Schedule training sessions
- [ ] Book training room with projector
- [ ] Ensure test environment is set up
- [ ] Create test user accounts
- [ ] Prepare sample data
- [ ] Print training materials

**1 Week Before**:
- [ ] Send calendar invites to participants
- [ ] Share pre-training materials
- [ ] Test all equipment
- [ ] Verify test accounts work
- [ ] Prepare certificates

**Day Before**:
- [ ] Review all modules
- [ ] Test live demos
- [ ] Prepare backup plans
- [ ] Print attendance sheets

**Day Of**:
- [ ] Arrive 30 minutes early
- [ ] Set up equipment
- [ ] Test projector and internet
- [ ] Arrange seating
- [ ] Have water and refreshments ready

#### Training Delivery Tips

**Engagement Techniques**:
- Ask questions frequently
- Use real-world examples
- Encourage questions
- Break into small groups for exercises
- Use humor appropriately

**Pacing**:
- Check for understanding before moving on
- Adjust speed based on participant needs
- Take breaks every 60-90 minutes
- Allow time for practice

**Handling Questions**:
- Repeat question for all to hear
- If unsure, say "Let me verify and get back to you"
- Park complex questions for later
- Encourage peer answers

**Dealing with Challenges**:

**Technical Issues**:
- Have backup laptop ready
- Know IT support contact
- Can continue with theoretical discussion while issue resolved

**Slow Learners**:
- Offer one-on-one help during breaks
- Provide additional practice time
- Schedule follow-up session

**Advanced Users**:
- Give them helper role
- Assign advanced exercises
- Let them explore features independently

#### Post-Training Activities

**Immediately After**:
- [ ] Collect feedback forms
- [ ] Grade assessments
- [ ] Issue certificates
- [ ] Send thank you email with resources

**Within 1 Week**:
- [ ] Review feedback
- [ ] Update training materials based on feedback
- [ ] Schedule follow-up sessions if needed
- [ ] Report completion to management

**Ongoing**:
- [ ] Monitor user adoption
- [ ] Offer support during initial use period
- [ ] Collect usage metrics
- [ ] Plan refresher training

### Training Environment Setup

**Test Database**:
- Separate from production
- Reset weekly
- Pre-loaded with sample data

**Test Accounts**:
```
Username: trainee01 to trainee20
Password: Train123! (change on first login)
Roles: Assigned based on session type
```

**Sample Data**:
- 50 bikes across multiple branches
- Various statuses (IN_STOCK, SOLD, IN_TRANSIT)
- Complete cost information
- Transfer examples
- Historical sales

---

## Quick Reference Cards

### Card 1: Adding a Bike

**QUICK GUIDE: ADD NEW BIKE**

1. **Navigate**
   Bikes > Acquisition

2. **Required Fields**
   - Company & Branch ⚠️
   - Title, Brand, Model ⚠️
   - Purchase Price ⚠️
   - Procurement Date

3. **Optional But Recommended**
   - License Plate
   - Supplier Info
   - Payment Method

4. **Submit**
   - Click "Submit"
   - Note stock number
   - Verify in inventory

**Tips**:
✓ Stock number auto-assigned
✓ Double-check price
✓ Verify license plate

---

### Card 2: Recording a Sale

**QUICK GUIDE: RECORD SALE**

1. **Find Bike**
   - Must be IN_STOCK
   - Click "Sell" button

2. **Sale Info** ⚠️
   - Selling Price
   - Customer Name
   - Customer Contact
   - Customer NIC
   - Payment Method

3. **Review P/L**
   ```
   Total Cost
   - Purchase
   - Repairs
   - Expenses

   Selling Price
   = Profit/Loss
   ```

4. **Submit**
   - Green = Profit ✓
   - Red = Loss (get approval)

**Tips**:
✓ Check P/L before submit
✓ Verify customer info
✓ Note commission

---

### Card 3: Transfer Process

**QUICK GUIDE: TRANSFERS**

**Creating Request**:
1. Find bike (IN_STOCK)
2. Click "Transfer"
3. Select destination branch
4. Add reason and notes
5. Submit

**Approving**:
1. Transfers > Pending
2. Review details
3. Approve/Reject
4. Add notes

**Completing**:
1. Transfers > In Transit
2. Mark as Delivered
3. Enter delivery date
4. Confirm

**Status Flow**:
REQUEST → PENDING → IN_TRANSIT → COMPLETED

---

### Card 4: Common Filters

**QUICK GUIDE: FINDING BIKES**

**By Status**:
- IN_STOCK = Available
- SOLD = Already sold
- IN_TRANSIT = Transferring
- ALLOCATED = Reserved

**By Location**:
- Select company (MA/IN)
- Select branch (WW/HP/BRC/etc)

**By Search**:
- Stock number: MA/WW/ST/2066
- License plate: ABC-1234
- Brand/model keywords

**Clear Filters**: Click "Clear All"

---

## Training Materials Checklist

### Printable Materials

- [ ] Training agenda
- [ ] Attendance sheet
- [ ] Participant list with credentials
- [ ] Quick reference cards (4 types)
- [ ] Exercise worksheets
- [ ] Assessment tests
- [ ] Feedback forms
- [ ] Certificate templates

### Digital Materials

- [ ] PowerPoint presentation slides
- [ ] Video tutorials (if available)
- [ ] Sample reports (PDF)
- [ ] User manual (PDF)
- [ ] Screen recording of demos

### Equipment Needed

- [ ] Projector and screen
- [ ] Trainer laptop
- [ ] Participant computers (1 per person)
- [ ] Internet connection
- [ ] Whiteboard and markers
- [ ] Printed materials
- [ ] Name tags
- [ ] Refreshments

---

## Feedback and Improvement

### Post-Training Feedback Form

**Training Evaluation**

Date: _______________
Module: _______________

Please rate the following (1 = Poor, 5 = Excellent):

1. Content was relevant and useful: 1 2 3 4 5
2. Trainer was knowledgeable: 1 2 3 4 5
3. Pace was appropriate: 1 2 3 4 5
4. Hands-on exercises were helpful: 1 2 3 4 5
5. I feel confident using the system: 1 2 3 4 5

**What did you like most?**
_________________________________

**What could be improved?**
_________________________________

**Additional training needed?**
_________________________________

**Comments/Suggestions:**
_________________________________

### Continuous Improvement

**Review Metrics**:
- Training completion rate
- Assessment scores
- Post-training system usage
- User-reported issues
- Time to competency

**Update Schedule**:
- Review feedback monthly
- Update materials quarterly
- Major revision annually

---

## Support After Training

### First Week Support

**Daily Check-Ins**:
- Trainer available for questions
- Quick help sessions
- Common issues documentation

**Slack/WhatsApp Group**:
- Create training cohort group
- Share tips and solutions
- Peer support encouraged

### Ongoing Support

**Office Hours**:
- Weekly 1-hour Q&A session
- Drop-in support
- Screen sharing for issues

**Resources**:
- User manual (always available)
- Video tutorial library
- FAQ document (updated regularly)

**Escalation Path**:
1. Check user manual
2. Ask trainer/colleagues
3. Submit support ticket
4. Call IT support

---

**Training Program Version**: 1.0.0
**Last Updated**: 2025-11-18
**Next Review**: 2025-12-18

**Questions?** Contact: training@yourdomain.com
