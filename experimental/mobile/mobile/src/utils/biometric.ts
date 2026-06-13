import * as LocalAuthentication from 'expo-local-authentication';
import * as SecureStore from 'expo-secure-store';

const BIOMETRIC_TOKEN_KEY = 'biometric_token';

export async function isBiometricAvailable(): Promise<boolean> {
  const compatible = await LocalAuthentication.hasHardwareAsync();
  if (!compatible) return false;

  const enrolled = await LocalAuthentication.isEnrolledAsync();
  return enrolled;
}

export async function authenticateWithBiometrics(): Promise<boolean> {
  const result = await LocalAuthentication.authenticateAsync({
    promptMessage: 'Log in to Infra Pilot',
    fallbackLabel: 'Use password',
    cancelLabel: 'Cancel',
  });

  return result.success;
}

export async function getBiometricTypes(): Promise<LocalAuthentication.AuthenticationType[]> {
  return LocalAuthentication.supportedAuthenticationTypesAsync();
}

export async function storeTokenForBiometric(token: string): Promise<void> {
  await SecureStore.setItemAsync(BIOMETRIC_TOKEN_KEY, token, {
    requireAuthentication: true,
  });
}

export async function getTokenFromBiometric(): Promise<string | null> {
  try {
    return await SecureStore.getItemAsync(BIOMETRIC_TOKEN_KEY, {
      requireAuthentication: true,
    });
  } catch {
    return null;
  }
}

export async function clearBiometricToken(): Promise<void> {
  await SecureStore.deleteItemAsync(BIOMETRIC_TOKEN_KEY);
}
