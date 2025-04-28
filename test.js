// test.js
const fetch = (...args) => import('node-fetch').then(({default: fetch}) => fetch(...args));

async function runPipeline() {
  // 1. Lancer le pipeline
  const response = await fetch('http://localhost:8080/pipelines/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      config: {
        input: {
          type: "csv",
          properties: {
            path: "tests/stubs/csv_rag/base_radio_manual.csv",
            target_column: "content",
            separator: "\t"
          }
        },
        pipeline: [
          {
            type: "split",
            method: "chunk",
            name: "chunk_faq",
            parameters: {
              size: 9999
            }
          },
          {
            type: "generation",
            method: "llm",
            parameters: {
              provider: "mistral",
              model: "mistral-large-latest",
              batch_size: 40,
              batch: true,
              template: `
                You are a human in a car looking for information about the vehicle.
                The question must be natural, like a question a human would ask in a typical request to a incar assistant.
                Ask a question about the content.
                content: {chunk_faq}

                Instructions :
                1. Use english only
                2. Keep it short

                Answer directly the question, do not add any other text.
              `
            }
          },
          {
            type: "clean",
            method: "deduplicate-embed",
            parameters: {
              provider: "mistral",
              model: "mistral-embed",
              similarity_threshold: 0.7
            }
          }
        ],
        output: {
          type: "csv",
          properties: {
            path: "tests/stubs/csv_rag/output_radio_manual_embed.csv",
            separator: "\t"
          }
        }
      }
    })
  });

  if (!response.ok) {
    const text = await response.text();
    console.error("Erreur HTTP:", response.status, text);
    return;
  }

  const { run_id } = await response.json();
  console.log("Run lancé avec l'ID:", run_id);

  // 2. Poller le résultat jusqu'à ce qu'il soit terminé
  let status = "pending";
  let result;
  while (status === "pending" || status === "running") {
    await new Promise(r => setTimeout(r, 1000)); // attendre 1s
    const res = await fetch(`http://localhost:8080/runs/${run_id}`);
    if (!res.ok) {
      console.error(`Erreur lors de la récupération du status (${res.status}):`, await res.text());
      return;
    }
    result = await res.json();
    status = result.status;
    console.log("Statut:", status);
  }

  // 3. Afficher le résultat final
  console.log("\n--- RÉSULTAT FINAL ---");
  console.log(`Statut: ${result.status} (code retour: ${result.returncode || 'N/A'})`);
  
  if (status === "completed") {
    console.log("\nSuccès!\n");
    console.log("Résultat:", result.result ? result.result.substring(0, 500) + "..." : "Aucun résultat");
  } else {
    console.log("\nÉchec!\n");
    
    if (result.command) {
      console.log("Commande exécutée:", result.command);
    }
    
    if (result.error) {
      console.log("\n--- ERREUR ---");
      console.log(result.error);
    }
    
    if (result.stderr && result.stderr.trim()) {
      console.log("\n--- STDERR ---");
      console.log(result.stderr);
    }
    
    if (result.stdout && result.stdout.trim()) {
      console.log("\n--- STDOUT ---");
      console.log(result.stdout);
    }
  }
}

runPipeline();