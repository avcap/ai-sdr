import pytest
from agents.workflow import AISDRWorkflow, CampaignData, LeadData
from datetime import datetime

def test_lead_data_validation():
    """Test LeadData model validation"""
    # Valid lead data
    lead = LeadData(
        name="John Doe",
        company="Test Company",
        title="Test Title",
        email="john@test.com"
    )
    assert lead.name == "John Doe"
    assert lead.company == "Test Company"
    assert lead.email == "john@test.com"

def test_campaign_data_validation():
    """Test CampaignData model validation"""
    campaign = CampaignData(
        campaign_id="test-001",
        name="Test Campaign",
        description="Test Description",
        target_audience="Test Audience",
        value_proposition="Test Value Prop",
        call_to_action="Test CTA",
        created_at=datetime.now()
    )
    assert campaign.campaign_id == "test-001"
    assert campaign.name == "Test Campaign"
    assert campaign.status == "draft"  # Default value

def test_workflow_creation():
    """Test AISDRWorkflow creation"""
    workflow = AISDRWorkflow()
    assert workflow.crew is None
    assert workflow.campaign_data is None

def test_workflow_crew_creation():
    """Test crew creation with sample data"""
    workflow = AISDRWorkflow()
    
    sample_leads = [
        {
            "name": "John Smith",
            "company": "TechCorp Inc",
            "title": "VP of Engineering",
            "email": "john@techcorp.com"
        }
    ]
    
    sample_campaign = CampaignData(
        campaign_id="test-001",
        name="Test Campaign",
        description="Test Description",
        target_audience="Test Audience",
        value_proposition="Test Value Prop",
        call_to_action="Test CTA",
        created_at=datetime.now()
    )
    
    crew = workflow.create_crew("test-001", sample_leads, sample_campaign)
    assert crew is not None
    assert workflow.campaign_data is not None
    assert len(crew.agents) == 4  # 4 agents: prospecting, personalization, outreach, coordinator
    assert len(crew.tasks) == 4  # 4 tasks

def test_prospecting_tool():
    """Test ProspectingTool functionality"""
    from agents.workflow import ProspectingTool
    
    tool = ProspectingTool()
    
    sample_leads = [
        {
            "name": "John Doe",
            "company": "Test Company",
            "title": "Test Title",
            "email": "john@test.com"
        },
        {
            "name": "Jane Doe",
            "company": "Another Company",
            "title": "Another Title"
            # Missing email - should still be valid
        }
    ]
    
    validated_leads = tool._run(sample_leads)
    assert len(validated_leads) == 2
    assert validated_leads[0].name == "John Doe"
    assert validated_leads[1].name == "Jane Doe"

def test_personalization_tool():
    """Test PersonalizationTool functionality"""
    from agents.workflow import PersonalizationTool
    
    tool = PersonalizationTool()
    
    lead = LeadData(
        name="John Doe",
        company="Test Company",
        title="VP of Engineering",
        email="john@test.com",
        industry="Technology"
    )
    
    campaign = CampaignData(
        campaign_id="test-001",
        name="AI Automation Campaign",
        description="Test Description",
        target_audience="Engineering Leaders",
        value_proposition="Our AI platform reduces manual work by 40%",
        call_to_action="Would you be open to a 15-minute call?",
        created_at=datetime.now()
    )
    
    message = tool._run(lead, campaign)
    
    assert "email_message" in message
    assert "linkedin_message" in message
    assert "personalization_score" in message
    
    # Check that personalization includes lead-specific information
    assert "John Doe" in message["email_message"]
    assert "Test Company" in message["email_message"]
    assert "VP of Engineering" in message["email_message"]
    
    # Check personalization score
    assert 0 <= message["personalization_score"] <= 1

def test_outreach_tool():
    """Test OutreachTool functionality"""
    from agents.workflow import OutreachTool
    
    tool = OutreachTool()
    
    lead = LeadData(
        name="John Doe",
        company="Test Company",
        title="VP of Engineering",
        email="john@test.com"
    )
    
    message = {
        "email_message": "Test email message",
        "linkedin_message": "Test LinkedIn message"
    }
    
    result = tool._run(lead, message, "email")
    
    assert "lead_id" in result
    assert "channel" in result
    assert "message_sent" in result
    assert "sent_at" in result
    assert result["channel"] == "email"
    assert result["message_sent"] is True

def test_coordinator_tool():
    """Test CoordinatorTool functionality"""
    from agents.workflow import CoordinatorTool
    
    tool = CoordinatorTool()
    
    leads = [
        LeadData(
            name="John Doe",
            company="Test Company",
            title="VP of Engineering",
            email="john@test.com"
        )
    ]
    
    campaign = CampaignData(
        campaign_id="test-001",
        name="Test Campaign",
        description="Test Description",
        target_audience="Test Audience",
        value_proposition="Test Value Prop",
        call_to_action="Test CTA",
        created_at=datetime.now()
    )
    
    result = tool._run("test-001", leads, campaign)
    
    assert "campaign_id" in result
    assert "total_leads" in result
    assert "processed_leads" in result
    assert "successful_outreach" in result
    assert result["campaign_id"] == "test-001"
    assert result["total_leads"] == 1

def test_workflow_execution_simulation():
    """Test complete workflow execution (simulation)"""
    workflow = AISDRWorkflow()
    
    sample_leads = [
        {
            "name": "John Smith",
            "company": "TechCorp Inc",
            "title": "VP of Engineering",
            "email": "john@techcorp.com",
            "industry": "Technology"
        },
        {
            "name": "Sarah Johnson",
            "company": "DataFlow Systems",
            "title": "CTO",
            "email": "sarah@dataflow.com",
            "industry": "Data Analytics"
        }
    ]
    
    sample_campaign = CampaignData(
        campaign_id="test-execution",
        name="AI Automation Outreach",
        description="Outreach campaign for AI automation services",
        target_audience="Engineering leaders at tech companies",
        value_proposition="Our AI automation platform can reduce your engineering team's manual work by 40%",
        call_to_action="Would you be open to a 15-minute call to discuss how this could work for your team?",
        created_at=datetime.now()
    )
    
    # Create crew
    crew = workflow.create_crew("test-execution", sample_leads, sample_campaign)
    assert crew is not None
    
    # Note: In a real test, we would mock the CrewAI execution
    # For now, we just verify the crew was created correctly
    assert len(crew.agents) == 4
    assert len(crew.tasks) == 4

def test_utility_functions():
    """Test utility functions"""
    from agents.workflow import load_leads_from_csv, save_campaign_results
    import tempfile
    import os
    
    # Test CSV loading (with temporary file)
    sample_csv_content = """name,company,title,email
John Doe,Test Company,VP Engineering,john@test.com
Jane Smith,Another Company,CTO,jane@another.com"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(sample_csv_content)
        temp_file = f.name
    
    try:
        leads = load_leads_from_csv(temp_file)
        assert len(leads) == 2
        assert leads[0]["name"] == "John Doe"
        assert leads[1]["name"] == "Jane Smith"
    finally:
        os.unlink(temp_file)
    
    # Test results saving
    test_results = {
        "status": "success",
        "campaign_id": "test-001",
        "executed_at": datetime.now().isoformat()
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_file = f.name
    
    try:
        save_campaign_results(test_results, temp_file)
        assert os.path.exists(temp_file)
        
        # Verify file content
        import json
        with open(temp_file, 'r') as f:
            saved_data = json.load(f)
        assert saved_data["status"] == "success"
        assert saved_data["campaign_id"] == "test-001"
    finally:
        os.unlink(temp_file)

if __name__ == "__main__":
    pytest.main([__file__])
