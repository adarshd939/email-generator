document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('email-form');
    const resultContainer = document.getElementById('result-container');
    const resultText = document.getElementById('result-text');
    const loadingIndicator = document.getElementById('loading-indicator');
    const generateBtn = document.getElementById('generate-btn');
    const copyBtn = document.getElementById('copy-btn');

    // --- Form Submission Handler ---
    form.addEventListener('submit', async (event) => {
        event.preventDefault();

        // 1. Get form values
        const goal = document.getElementById('goal').value;
        const recipient = document.getElementById('recipient').value;
        const tone = document.getElementById('tone').value;
        const points = document.getElementById('points').value;

        // 2. Update UI for loading state
        resultContainer.classList.remove('hidden');
        loadingIndicator.classList.remove('hidden');
        resultText.textContent = '';
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="fa-solid fa-hourglass-half"></i> Generating...';

        try {
            // 3. Make API call
            const response = await fetch('/api/generate-email', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ goal, recipient, tone, points }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'An unknown error occurred.');
            }
            
            // 4. Display result
            const data = await response.json();
            resultText.textContent = data.generated_email.trim();

        } catch (error) {
            resultText.textContent = `Error: ${error.message}`;
            resultText.style.color = '#e94560'; // Style error text
        } finally {
            // 5. Reset UI after completion
            loadingIndicator.classList.add('hidden');
            generateBtn.disabled = false;
            generateBtn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Generate Email';
        }
    });
    
    // --- Copy to Clipboard Handler ---
    copyBtn.addEventListener('click', () => {
        if (resultText.textContent) {
            navigator.clipboard.writeText(resultText.textContent)
                .then(() => {
                    // Provide user feedback on successful copy
                    copyBtn.innerHTML = '<i class="fa-solid fa-check"></i> Copied!';
                    setTimeout(() => {
                        copyBtn.innerHTML = '<i class="fa-regular fa-copy"></i> Copy';
                    }, 2000);
                })
                .catch(err => {
                    console.error('Failed to copy text: ', err);
                    // Optionally, provide an error message to the user
                    copyBtn.textContent = 'Failed!';
                     setTimeout(() => {
                        copyBtn.innerHTML = '<i class="fa-regular fa-copy"></i> Copy';
                    }, 2000);
                });
        }
    });
});