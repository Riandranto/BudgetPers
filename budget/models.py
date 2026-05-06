from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Category(models.Model):
    TYPE_CHOICES = (
        ('income', 'Revenu'),
        ('expense', 'Dépense'),
    )
    
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='expense')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')
    color = models.CharField(max_length=7, default='#2d6a4f', help_text="Couleur en hexadécimal")
    icon = models.CharField(max_length=50, default='fa-tag', help_text="Icône FontAwesome")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['name', 'user']
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Transaction(models.Model):
    TYPE_CHOICES = (
        ('income', 'Revenu'),
        ('expense', 'Dépense'),
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='transactions')
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    description = models.TextField(blank=True)
    date = models.DateField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_type_display()} - {self.amount} Ar - {self.date}"

class Budget(models.Model):
    PERIOD_CHOICES = (
        ('monthly', 'Mensuel'),
        ('weekly', 'Hebdomadaire'),
        ('yearly', 'Annuel'),
    )
    
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='budgets')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES, default='monthly')
    month = models.IntegerField(null=True, blank=True, help_text="Mois (1-12)")
    year = models.IntegerField(default=timezone.now().year)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['category', 'user', 'period', 'month', 'year']
    
    def get_spent_amount(self):
        """Calcule le montant dépensé pour ce budget"""
        transactions = self.category.transactions.filter(
            type='expense',
            user=self.user,
            date__year=self.year
        )
        if self.period == 'monthly' and self.month:
            transactions = transactions.filter(date__month=self.month)
        return transactions.aggregate(total=models.Sum('amount'))['total'] or 0
    
    def get_remaining_amount(self):
        return self.amount - self.get_spent_amount()
    
    def get_percentage_used(self):
        if self.amount > 0:
            return (self.get_spent_amount() / self.amount) * 100
        return 0

    def __str__(self):
        return f"Budget {self.category.name} - {self.amount} Ar ({self.get_period_display()})"

class SavingGoal(models.Model):
    STATUS_CHOICES = (
        ('active', 'Actif'),
        ('completed', 'Atteint'),
        ('cancelled', 'Annulé'),
    )
    
    name = models.CharField(max_length=200)
    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deadline = models.DateField()
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saving_goals')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def get_progress_percentage(self):
        if self.target_amount > 0:
            return (self.current_amount / self.target_amount) * 100
        return 0
    
    def get_remaining_amount(self):
        return self.target_amount - self.current_amount
    
    def is_completed(self):
        return self.current_amount >= self.target_amount
    
    def __str__(self):
        return f"{self.name} - {self.get_progress_percentage():.1f}%"