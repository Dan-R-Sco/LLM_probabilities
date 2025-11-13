document.addEventListener('DOMContentLoaded', () => {
    const promptInput = document.getElementById('prompt-input');
    const generateBtn = document.getElementById('generate-btn');
    const loading = document.getElementById('loading');
    const responseOutput = document.getElementById('response-output');
    const tooltip = document.getElementById('tooltip');

    generateBtn.addEventListener('click', async () => {
        const prompt = promptInput.value;
        if (!prompt) {
            alert('Please enter a prompt.');
            return;
        }

        loading.classList.remove('hidden');
        responseOutput.innerHTML = '';

        try {
            const response = await fetch('/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ prompt }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'An error occurred.');
            }

            const data = await response.json();
            console.log('Received data from server:', data); // For debugging
            displayResponse(data);

        } catch (error) {
            responseOutput.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
        } finally {
            loading.classList.add('hidden');
        }
    });

    function displayResponse(data) {
        responseOutput.innerHTML = ''; // Clear previous response
        const tokens = data.response;

        console.log('Number of tokens received:', tokens.length);
        console.log('Full data object:', data);

        // If no token data but we have text, display the text
        if (!tokens || tokens.length === 0) {
            if (data.text) {
                responseOutput.innerHTML = `<p>${data.text}</p><p style="color: orange; font-size: 0.9em; margin-top: 10px;">⚠️ Note: Token probabilities not available for this response.</p>`;
            } else {
                responseOutput.innerHTML = '<p style="color: red;">No response data received.</p>';
            }
            return;
        }

        tokens.forEach(tokenData => {
            const span = document.createElement('span');
            span.textContent = tokenData.token;
            span.dataset.probability = tokenData.probability;
            span.dataset.top5 = JSON.stringify(tokenData.top_5);

            span.addEventListener('mousemove', (e) => {
                const probability = parseFloat(span.dataset.probability).toFixed(4);
                const top5 = JSON.parse(span.dataset.top5);

                let tooltipContent = `<strong>Probability:</strong> ${probability}<br>`;
                tooltipContent += '<strong>Top 5 Alternatives:</strong><ul>';
                for (const [token, prob] of Object.entries(top5)) {
                    tooltipContent += `<li>${token}: ${prob.toFixed(4)}</li>`;
                }
                tooltipContent += '</ul>';

                tooltip.innerHTML = tooltipContent;
                tooltip.classList.remove('hidden');
                tooltip.style.left = `${e.pageX + 10}px`;
                tooltip.style.top = `${e.pageY + 10}px`;
            });

            span.addEventListener('mouseout', () => {
                tooltip.classList.add('hidden');
            });

            responseOutput.appendChild(span);
        });
    }
});
