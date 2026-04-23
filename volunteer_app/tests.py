from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from .models import (
    Activity, ActivitySignup, QRScan, IdeaProposal, IdeaVote,
    Group, GroupMembership
)
from .utils import make_qr_token, verify_qr_token

User = get_user_model()


class UserModelTests(TestCase):
    """Tests for User model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@ubu.ac.th",
            password="testpass123"
        )
    
    def test_user_creation(self):
        """Test user can be created"""
        self.assertEqual(self.user.username, "testuser")
        self.assertEqual(self.user.email, "test@ubu.ac.th")
    
    def test_total_hours_calculation(self):
        """Test total_hours() method calculates correctly"""
        # Create activity and QR scan
        activity = Activity.objects.create(
            title="Test Activity",
            datetime=timezone.now(),
            location="Test Location",
            hours_reward=2.5
        )
        QRScan.objects.create(
            activity=activity,
            user=self.user,
            token="test_token"
        )
        
        self.assertEqual(self.user.total_hours(), 2.5)


class ActivityModelTests(TestCase):
    """Tests for Activity model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="admin",
            email="admin@ubu.ac.th",
            password="admin123"
        )
        self.activity = Activity.objects.create(
            title="Test Activity",
            datetime=timezone.now(),
            location="Test Location",
            capacity=10,
            hours_reward=3.0,
            created_by=self.user
        )
    
    def test_activity_creation(self):
        """Test activity can be created"""
        self.assertEqual(self.activity.title, "Test Activity")
        self.assertEqual(self.activity.capacity, 10)
        self.assertEqual(self.activity.hours_reward, 3.0)
    
    def test_is_full(self):
        """Test is_full() method"""
        self.assertFalse(self.activity.is_full())
        
        # Create signups up to capacity
        for i in range(10):
            user = User.objects.create_user(
                username=f"user{i}",
                email=f"user{i}@ubu.ac.th",
                password="test123"
            )
            ActivitySignup.objects.create(
                activity=self.activity,
                user=user,
                status="confirmed"
            )
        
        self.assertTrue(self.activity.is_full())


class QRTokenTests(TestCase):
    """Tests for QR Token generation and verification"""
    
    def setUp(self):
        self.activity_id = 1
    
    def test_qr_token_generation(self):
        """Test QR token can be generated"""
        token = make_qr_token(self.activity_id)
        self.assertIsNotNone(token)
    
    def test_qr_token_verification(self):
        """Test QR token verification"""
        token = make_qr_token(self.activity_id, expires_in=3600)
        valid, activity_id = verify_qr_token(token)
        
        self.assertTrue(valid)
        self.assertEqual(activity_id, self.activity_id)
    
    def test_invalid_qr_token(self):
        """Test invalid QR token returns False"""
        valid, activity_id = verify_qr_token("invalid_token")
        self.assertFalse(valid)
        self.assertIsNone(activity_id)


class RegistrationTests(TestCase):
    """Tests for user registration"""
    
    def setUp(self):
        self.client = Client()
        self.register_url = reverse("volunteer_app:register")
    
    def test_registration_page_loads(self):
        """Test registration page loads successfully"""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
    
    def test_registration_with_valid_email(self):
        """Test registration with valid @ubu.ac.th email"""
        data = {
            "username": "newuser",
            "email": "newuser@ubu.ac.th",
            "title": "นาย",
            "first_name": "Test",
            "last_name": "User",
            "student_id": "12345",
            "faculty": "คณะทดสอบ",
            "department": "สาขาทดสอบ",
            "year": 3,
            "password1": "testpass123",
            "password2": "testpass123",
        }
        
        response = self.client.post(self.register_url, data)
        # Should redirect after successful registration
        self.assertIn(response.status_code, [200, 302])
        
        # Check user was created
        user = User.objects.filter(email="newuser@ubu.ac.th").first()
        self.assertIsNotNone(user)


class IdeaVoteTests(TestCase):
    """Tests for Idea Voting"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="voter",
            email="voter@ubu.ac.th",
            password="test123"
        )
        self.proposer = User.objects.create_user(
            username="proposer",
            email="proposer@ubu.ac.th",
            password="test123"
        )
        self.idea = IdeaProposal.objects.create(
            proposer=self.proposer,
            title="Test Idea",
            description="Test Description",
            target_hours=5.0
        )
    
    def test_idea_creation(self):
        """Test idea can be created"""
        self.assertEqual(self.idea.title, "Test Idea")
        self.assertEqual(self.idea.status, "pending")
    
    def test_idea_vote(self):
        """Test user can vote for idea"""
        vote = IdeaVote.objects.create(
            idea=self.idea,
            user=self.user
        )
        
        self.assertEqual(self.idea.votes.count(), 1)
        self.assertEqual(self.idea.total_votes(), 1)
    
    def test_duplicate_vote_prevention(self):
        """Test user cannot vote twice for same idea"""
        IdeaVote.objects.create(
            idea=self.idea,
            user=self.user
        )
        
        # Try to create duplicate vote
        with self.assertRaises(Exception):
            IdeaVote.objects.create(
                idea=self.idea,
                user=self.user
            )


class GroupTests(TestCase):
    """Tests for Group functionality"""
    
    def setUp(self):
        self.creator = User.objects.create_user(
            username="creator",
            email="creator@ubu.ac.th",
            password="test123"
        )
        self.group = Group.objects.create(
            name="Test Group",
            description="Test Description",
            code="testcode123",
            created_by=self.creator
        )
    
    def test_group_creation(self):
        """Test group can be created"""
        self.assertEqual(self.group.name, "Test Group")
        self.assertEqual(self.group.created_by, self.creator)
    
    def test_group_membership(self):
        """Test user can join group"""
        membership = GroupMembership.objects.create(
            group=self.group,
            user=self.creator
        )
        
        self.assertTrue(self.group.is_member(self.creator))
        self.assertEqual(self.group.member_count(), 1)


class ViewTests(TestCase):
    """Tests for views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@ubu.ac.th",
            password="testpass123"
        )
    
    def test_index_page_loads(self):
        """Test index page loads"""
        response = self.client.get(reverse("volunteer_app:index"))
        self.assertEqual(response.status_code, 200)
    
    def test_profile_requires_login(self):
        """Test profile page requires login"""
        response = self.client.get(reverse("volunteer_app:profile"))
        self.assertRedirects(response, f"/accounts/login/?next={reverse('volunteer_app:profile')}")
    
    def test_profile_accessible_when_logged_in(self):
        """Test profile page accessible when logged in"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("volunteer_app:profile"))
        self.assertEqual(response.status_code, 200)
