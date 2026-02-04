/**
 * Script de teste para verificar conexão com a API
 * Execute: node test-api-connection.js
 */

const API_URL = 'http://localhost:8000';

async function testAPIConnection() {
  console.log('🧪 Testando conexão com a API...\n');

  try {
    // 1. Testar health check
    console.log('1️⃣  Testando health check...');
    const healthResponse = await fetch(`${API_URL}/health`);
    const healthData = await healthResponse.json();
    console.log('✅ Health check:', healthData);

    // 2. Testar listagem de leads
    console.log('\n2️⃣  Testando GET /api/leads...');
    const leadsResponse = await fetch(`${API_URL}/api/leads`);
    const leads = await leadsResponse.json();
    console.log(`✅ ${leads.length} leads encontrados`);

    // Mostrar primeiros 3 leads
    console.log('\nPrimeiros 3 leads:');
    leads.slice(0, 3).forEach((lead, index) => {
      console.log(`  ${index + 1}. ${lead.nome} (${lead.empresa || 'Sem empresa'})`);
      console.log(`     Status: ${lead.status} | Score: ${lead.lead_score}`);
    });

    // 3. Testar estatísticas
    console.log('\n3️⃣  Testando GET /api/leads/stats/summary...');
    const statsResponse = await fetch(`${API_URL}/api/leads/stats/summary`);
    const stats = await statsResponse.json();
    console.log('✅ Estatísticas:');
    console.log(`   Total de leads: ${stats.total_leads}`);
    console.log(`   Score médio: ${stats.score_medio}`);
    console.log(`   Pipeline: R$ ${stats.valor_total_pipeline.toLocaleString('pt-BR')}`);
    console.log(`   Taxa de conversão: ${stats.taxa_conversao}%`);

    console.log('\n✅ TODOS OS TESTES PASSARAM!');
    console.log('🚀 O frontend pode consumir a API sem problemas.\n');

  } catch (error) {
    console.error('\n❌ ERRO:', error.message);
    console.error('\n🔧 Verifique:');
    console.error('   1. O backend está rodando? (python -m uvicorn app.main:app --reload)');
    console.error('   2. A URL está correta? (http://localhost:8000)');
    console.error('   3. O CORS está configurado?\n');
    process.exit(1);
  }
}

testAPIConnection();
