from django.urls import path
from . import views

urlpatterns = [
    #HOME
    path('', views.home, name='home'),
    
    # Alunos
    path('alunos/', views.listar_alunos, name='listar_alunos'),
    path('alunos/cadastro/', views.cadastrar_aluno, name='cadastrar_aluno'),
    path('alunos/<str:cpf>/editar/', views.editar_aluno, name='editar_aluno'),
    path('alunos/<str:cpf>/', views.detalhe_aluno, name='detalhe_aluno'),
    path('alunos/<str:cpf>/excluir/', views.excluir_aluno, name='excluir_aluno'),

    # Pagamentos
    path('pagamentos/', views.listar_pagamentos, name='listar_pagamentos'),
    path('pagamentos/criar/', views.criar_pagamento, name='criar_pagamento'),
    path('pagamentos/<int:cod_pagamento>/editar/', views.editar_pagamento, name='editar_pagamento'),
    path('pagamentos/<int:cod_pagamento>/', views.detalhe_pagamento, name='detalhe_pagamento'),
    
    # Turmas
    path('turmas/', views.listar_turmas, name='listar_turmas'),
    path('turmas/criar/', views.criar_turma, name='criar_turma'),
    path('turmas/<int:cod_turma>/editar/', views.editar_turma, name='editar_turma'),
    path('turmas/<int:cod_turma>/', views.detalhe_turma, name='detalhe_turma'),
    path('turmas/<int:cod_turma>/excluir/', views.excluir_turma, name='excluir_turma'),

    # Inscrições
    path('turmas/<int:cod_turma>/inscrever/', views.inscrever_aluno, name='inscrever_aluno'),
    path('turmas/<int:cod_turma>/cancelar/<str:cpf_aluno>/', views.cancelar_inscricao, name='cancelar_inscricao'),
    
    #Professores
    path('professores/', views.listar_professores, name='listar_professores'),
    path('professores/<str:cref>/', views.detalhe_professor, name='detalhe_professor'),
    
    #Unidades
    path('unidades/', views.listar_unidades, name='listar_unidades'),
    path('unidades/<int:cod_unidade>/', views.detalhe_unidade, name='detalhe_unidade'),
]
