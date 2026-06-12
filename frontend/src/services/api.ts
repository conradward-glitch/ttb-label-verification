import type { ApplicationData, VerificationResult } from '../types';

export async function verifyLabel(image: File, applicationData: ApplicationData): Promise<VerificationResult> {
  const formData = new FormData();
  formData.append('label_image', image);
  formData.append('application_data', JSON.stringify(applicationData));

  const response = await fetch('/api/verify', {
    method: 'POST',
    body: formData
  });

  if (!response.ok) {
    let message = 'Verification failed. Please try again.';
    try {
      const payload = await response.json();
      message = payload.detail || message;
    } catch {
      // keep fallback
    }
    throw new Error(message);
  }

  return response.json();
}
