// app/static/js/investment_charts.js

// Função para obter a cor do texto com base no tema do DaisyUI
function getChartTextColor() {
    // Acedemos ao atributo 'data-theme' na tag <html>
    const theme = document.documentElement.getAttribute('data-theme');
    // Retornamos uma cor para temas escuros e outra para temas claros
    return theme === 'dark' ? '#d1d5db' : '#374151';
}

// Função para inicializar o gráfico de Alocação por Ativo
function initAssetAllocationChart() {
    const ctx = document.getElementById('assetAllocationChart');
    if (!ctx) return; // Se o elemento não existir na página, não faz nada

    // Lê os dados JSON dos atributos data-* do canvas
    const labels = JSON.parse(ctx.dataset.labels);
    const data = JSON.parse(ctx.dataset.data);

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: ['#3b82f6', '#10b981', '#f97316', '#ef4444', '#8b5cf6', '#ec4899', '#f59e0b', '#14b8a6'],
                borderColor: 'hsl(var(--b1))',
                borderWidth: 2
            }]
        },
        options: { 
            responsive: true, 
            plugins: { 
                legend: { 
                    position: 'top',
                    labels: { color: getChartTextColor() } 
                } 
            } 
        }
    });
}

// Função para inicializar o gráfico de Crescimento do Capital
function initCapitalGrowthChart() {
    const ctx = document.getElementById('capitalGrowthChart');
    if (!ctx) return; // Se o elemento não existir na página, não faz nada

    const labels = JSON.parse(ctx.dataset.labels);
    const data = JSON.parse(ctx.dataset.data);

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Valor Investido Acumulado',
                data: data,
                fill: true,
                borderColor: '#3b82f6',
                tension: 0.1,
                backgroundColor: 'rgba(59, 130, 246, 0.2)'
            }]
        },
        options: { 
            responsive: true, 
            plugins: { 
                legend: { 
                    display: false 
                }
            },
            scales: {
                y: { ticks: { color: getChartTextColor() } },
                x: { ticks: { color: getChartTextColor() } }
            }
        }
    });
}


// Quando o documento HTML estiver totalmente carregado, executa as funções para criar os gráficos.
document.addEventListener('DOMContentLoaded', function() {
    initAssetAllocationChart();
    initCapitalGrowthChart();
});