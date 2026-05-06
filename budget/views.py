from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from django.forms import modelformset_factory
from datetime import datetime, timedelta
from .models import Transaction, Category, Budget, SavingGoal
from .forms import TransactionForm, TransactionFormSet, CategoryForm, BudgetForm, SavingGoalForm

# Authentication Views
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Inscription réussie ! Bienvenue !')
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'budget/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Bonjour {username} !')
                return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'budget/login.html', {'form': form})

# Dashboard
@login_required
def dashboard(request):
    today = timezone.now().date()
    current_month = today.month
    current_year = today.year
    
    # Statistiques du mois
    monthly_transactions = Transaction.objects.filter(
        user=request.user,
        date__year=current_year,
        date__month=current_month
    )
    
    total_income = monthly_transactions.filter(type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = monthly_transactions.filter(type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    balance = total_income - total_expense
    
    # Dépenses par catégorie
    expenses_by_category = monthly_transactions.filter(type='expense').values(
        'category__name', 'category__color'
    ).annotate(total=Sum('amount')).order_by('-total')[:5]
    
    # Transations récentes
    recent_transactions = monthly_transactions.order_by('-date')[:10]
    
    # Objectifs d'épargne
    saving_goals = SavingGoal.objects.filter(user=request.user, status='active')
    
    # Budgets du mois
    monthly_budgets = Budget.objects.filter(
        user=request.user,
        period='monthly',
        month=current_month,
        year=current_year
    )
    
    context = {
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': balance,
        'expenses_by_category': expenses_by_category,
        'recent_transactions': recent_transactions,
        'saving_goals': saving_goals,
        'monthly_budgets': monthly_budgets,
        'current_month': datetime(current_year, current_month, 1).strftime('%B %Y'),
    }
    return render(request, 'budget/dashboard.html', context)

# Transaction Views
@login_required
def transaction_list(request):
    transactions = Transaction.objects.filter(user=request.user).order_by('-date')
    return render(request, 'budget/list.html', {'transactions': transactions})

@login_required
def transaction_create(request):
    TransactionFormSet = modelformset_factory(Transaction, form=TransactionForm, extra=3)

    if request.method == 'POST':
        formset = TransactionFormSet(request.POST)
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.user = request.user
                instance.save()
            messages.success(request, 'Transactions ajoutées avec succès !')
            return redirect('transaction_list')
    else:
        formset = TransactionFormSet(queryset=Transaction.objects.none())
        # Ajouter l'utilisateur au formulaire
        for form in formset:
            form.user = request.user

    return render(request, 'budget/form.html', {'formset': formset})

@login_required
def transaction_update(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)

    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Transaction modifiée avec succès !')
            return redirect('transaction_list')
    else:
        form = TransactionForm(instance=transaction, user=request.user)
    return render(request, 'budget/update.html', {'form': form})

@login_required
def transaction_delete(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)

    if request.method == 'POST':
        transaction.delete()
        messages.success(request, 'Transaction supprimée avec succès !')
        return redirect('transaction_list')

    return render(request, 'budget/delete.html', {'transaction': transaction})

# Category Views
@login_required
def category_list(request):
    categories = Category.objects.filter(user=request.user)
    return render(request, 'budget/categories.html', {'categories': categories})

@login_required
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            messages.success(request, 'Catégorie créée avec succès !')
            return redirect('category_list')
    else:
        form = CategoryForm()
    return render(request, 'budget/category_form.html', {'form': form, 'title': 'Créer une catégorie'})

@login_required
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Catégorie modifiée avec succès !')
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'budget/category_form.html', {'form': form, 'title': 'Modifier la catégorie'})

@login_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Catégorie supprimée avec succès !')
        return redirect('category_list')
    return render(request, 'budget/category_confirm_delete.html', {'category': category})

# Budget Views
@login_required
def budget_list(request):
    budgets = Budget.objects.filter(user=request.user)
    for budget in budgets:
        budget.spent = budget.get_spent_amount()
        budget.remaining = budget.get_remaining_amount()
        budget.percentage = budget.get_percentage_used()
    return render(request, 'budget/budgets.html', {'budgets': budgets})

@login_required
def budget_create(request):
    if request.method == 'POST':
        form = BudgetForm(request.POST, user=request.user)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.user = request.user
            budget.save()
            messages.success(request, 'Budget créé avec succès !')
            return redirect('budget_list')
    else:
        form = BudgetForm(user=request.user)
    return render(request, 'budget/budget_form.html', {'form': form, 'title': 'Créer un budget'})

@login_required
def budget_update(request, pk):
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=budget, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Budget modifié avec succès !')
            return redirect('budget_list')
    else:
        form = BudgetForm(instance=budget, user=request.user)
    return render(request, 'budget/budget_form.html', {'form': form, 'title': 'Modifier le budget'})

@login_required
def budget_delete(request, pk):
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    if request.method == 'POST':
        budget.delete()
        messages.success(request, 'Budget supprimé avec succès !')
        return redirect('budget_list')
    return render(request, 'budget/budget_confirm_delete.html', {'budget': budget})

# Report Views
@login_required
def report_list(request):
    from django.db.models.functions import TruncMonth
    from datetime import datetime
    
    current_year = datetime.now().year
    
    # Statistiques annuelles
    monthly_stats = Transaction.objects.filter(
        user=request.user,
        date__year=current_year
    ).annotate(
        month=TruncMonth('date')
    ).values('month').annotate(
        income=Sum('amount', filter=Q(type='income')),
        expense=Sum('amount', filter=Q(type='expense'))
    ).order_by('month')
    
    # Top catégories de dépenses
    top_expense_categories = Transaction.objects.filter(
        user=request.user,
        type='expense',
        date__year=current_year
    ).values('category__name').annotate(
        total=Sum('amount')
    ).order_by('-total')[:10]
    
    context = {
        'monthly_stats': monthly_stats,
        'top_expense_categories': top_expense_categories,
        'current_year': current_year,
    }
    return render(request, 'budget/reports.html', context)

# Saving Goal Views
@login_required
def goal_list(request):
    goals = SavingGoal.objects.filter(user=request.user)
    for goal in goals:
        goal.progress = goal.get_progress_percentage()
        goal.remaining = goal.get_remaining_amount()
    return render(request, 'budget/goals.html', {'goals': goals})

@login_required
def goal_create(request):
    if request.method == 'POST':
        form = SavingGoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            messages.success(request, 'Objectif créé avec succès !')
            return redirect('goal_list')
    else:
        form = SavingGoalForm()
    return render(request, 'budget/goal_form.html', {'form': form, 'title': 'Créer un objectif'})

@login_required
def goal_update(request, pk):
    goal = get_object_or_404(SavingGoal, pk=pk, user=request.user)
    if request.method == 'POST':
        form = SavingGoalForm(request.POST, instance=goal)
        if form.is_valid():
            form.save()
            messages.success(request, 'Objectif modifié avec succès !')
            return redirect('goal_list')
    else:
        form = SavingGoalForm(instance=goal)
    return render(request, 'budget/goal_form.html', {'form': form, 'title': 'Modifier l\'objectif'})

@login_required
def goal_delete(request, pk):
    goal = get_object_or_404(SavingGoal, pk=pk, user=request.user)
    if request.method == 'POST':
        goal.delete()
        messages.success(request, 'Objectif supprimé avec succès !')
        return redirect('goal_list')
    return render(request, 'budget/goal_confirm_delete.html', {'goal': goal})

@login_required
def goal_add_amount(request, pk):
    goal = get_object_or_404(SavingGoal, pk=pk, user=request.user)
    if request.method == 'POST':
        amount = float(request.POST.get('amount', 0))
        if amount > 0:
            goal.current_amount += amount
            if goal.current_amount >= goal.target_amount:
                goal.status = 'completed'
            goal.save()
            messages.success(request, f'{amount:,.0f} Ar ajoutés à votre objectif !')
        return redirect('goal_list')
    return render(request, 'budget/goal_add_amount.html', {'goal': goal})