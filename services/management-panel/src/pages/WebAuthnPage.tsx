import { useEffect, useState } from 'react';
import { FormattedMessage, useIntl } from 'react-intl';
import { apiClient } from '../lib/api';
import { toast } from 'sonner';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Label } from '../components/ui/label';

interface Authenticator {
  authenticator_id: string;
  device_name: string;
  credential_id: string;
  created_at: string;
  last_used: string | null;
}

interface PasskeyChallenge {
  challenge_id: string;
  rp_id: string;
  expires_at: string;
}

export const WebAuthnPage = () => {
  const intl = useIntl();
  const [authenticators, setAuthenticators] = useState<Authenticator[]>([]);
  const [challenges, setChallenges] = useState<PasskeyChallenge[]>([]);
  const [loading, setLoading] = useState(true);
  const [newDeviceName, setNewDeviceName] = useState('');
  const [showRegisterDialog, setShowRegisterDialog] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState('current-user');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [authData, challengeData] = await Promise.all([
        apiClient.listAuthenticators(selectedUserId),
        apiClient.listPasskeyChallenges(selectedUserId),
      ]);
      setAuthenticators(authData || []);
      setChallenges(challengeData || []);
    } catch (error) {
      toast.error('Failed to load WebAuthn data');
    } finally {
      setLoading(false);
    }
  };

  const registerAuthenticator = async () => {
    try {
      const auth = await apiClient.registerAuthenticator({
        user_id: selectedUserId,
        device_name: newDeviceName,
      });
      setAuthenticators([...authenticators, auth]);
      toast.success('Authenticator registered');
      setShowRegisterDialog(false);
      setNewDeviceName('');
    } catch (error) {
      toast.error('Failed to register authenticator');
    }
  };

  const removeAuthenticator = async (id: string) => {
    try {
      await apiClient.removeAuthenticator(id);
      setAuthenticators(authenticators.filter((a) => a.authenticator_id !== id));
      toast.success('Authenticator removed');
    } catch (error) {
      toast.error('Failed to remove authenticator');
    }
  };

  const createChallenge = async () => {
    try {
      const challenge = await apiClient.createPasskeyChallenge({
        user_id: selectedUserId,
        relying_party: window.location.hostname,
      });
      setChallenges([...challenges, challenge]);
      toast.success('Passkey challenge created');
    } catch (error) {
      toast.error('Failed to create challenge');
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold"><FormattedMessage id="webauthn.title" defaultMessage="WebAuthn & Passkeys" /></h1>
          <p className="text-muted-foreground mt-1"><FormattedMessage id="webauthn.description" defaultMessage="Manage FIDO2 WebAuthn authenticators and passkey challenges" /></p>
        </div>
      </div>

      <Tabs defaultValue="authenticators">
        <TabsList>
          <TabsTrigger value="authenticators"><FormattedMessage id="webauthn.authenticators" defaultMessage="Authenticators" /></TabsTrigger>
          <TabsTrigger value="challenges"><FormattedMessage id="webauthn.challenges" defaultMessage="Passkey Challenges" /></TabsTrigger>
        </TabsList>

        <TabsContent value="authenticators" className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold"><FormattedMessage id="webauthn.registeredDevices" defaultMessage="Registered Devices" /></h2>
            <Dialog open={showRegisterDialog} onOpenChange={setShowRegisterDialog}>
              <DialogTrigger asChild>
                <Button><FormattedMessage id="webauthn.registerDevice" defaultMessage="Register Device" /></Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle><FormattedMessage id="webauthn.registerNew" defaultMessage="Register New Authenticator" /></DialogTitle>
                  <DialogDescription><FormattedMessage id="webauthn.registerDesc" defaultMessage="Register a new FIDO2 WebAuthn authenticator" /></DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <Label><FormattedMessage id="webauthn.deviceName" defaultMessage="Device Name" /></Label>
                    <Input value={newDeviceName} onChange={(e) => setNewDeviceName(e.target.value)} placeholder="YubiKey 5 NFC" />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setShowRegisterDialog(false)}><FormattedMessage id="common.cancel" defaultMessage="Cancel" /></Button>
                  <Button onClick={registerAuthenticator}><FormattedMessage id="webauthn.register" defaultMessage="Register" /></Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead><FormattedMessage id="webauthn.deviceName" defaultMessage="Device Name" /></TableHead>
                    <TableHead><FormattedMessage id="webauthn.credentialId" defaultMessage="Credential ID" /></TableHead>
                    <TableHead><FormattedMessage id="common.created" defaultMessage="Created" /></TableHead>
                    <TableHead><FormattedMessage id="webauthn.lastUsed" defaultMessage="Last Used" /></TableHead>
                    <TableHead><FormattedMessage id="common.actions" defaultMessage="Actions" /></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {authenticators.map((auth) => (
                    <TableRow key={auth.authenticator_id}>
                      <TableCell className="font-medium">{auth.device_name}</TableCell>
                      <TableCell className="font-mono text-xs">{auth.credential_id.substring(0, 20)}...</TableCell>
                      <TableCell>{new Date(auth.created_at).toLocaleDateString()}</TableCell>
                      <TableCell>{auth.last_used ? new Date(auth.last_used).toLocaleDateString() : 'Never'}</TableCell>
                      <TableCell>
                        <Button variant="destructive" size="sm" onClick={() => removeAuthenticator(auth.authenticator_id)}><FormattedMessage id="common.remove" defaultMessage="Remove" /></Button>
                      </TableCell>
                    </TableRow>
                  ))}
                  {authenticators.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                        <FormattedMessage id="webauthn.noDevices" defaultMessage="No authenticators registered" />
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="challenges" className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold"><FormattedMessage id="webauthn.passkeyChallenges" defaultMessage="Passkey Challenges" /></h2>
            <Button onClick={createChallenge}><FormattedMessage id="webauthn.createChallenge" defaultMessage="Create Challenge" /></Button>
          </div>
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead><FormattedMessage id="webauthn.challengeId" defaultMessage="Challenge ID" /></TableHead>
                    <TableHead><FormattedMessage id="webauthn.relyingParty" defaultMessage="Relying Party" /></TableHead>
                    <TableHead><FormattedMessage id="webauthn.expiresAt" defaultMessage="Expires At" /></TableHead>
                    <TableHead><FormattedMessage id="common.status" defaultMessage="Status" /></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {challenges.map((ch) => (
                    <TableRow key={ch.challenge_id}>
                      <TableCell className="font-mono text-xs">{ch.challenge_id.substring(0, 16)}...</TableCell>
                      <TableCell>{ch.rp_id}</TableCell>
                      <TableCell>{new Date(ch.expires_at).toLocaleString()}</TableCell>
                      <TableCell><Badge variant={new Date(ch.expires_at) > new Date() ? 'default' : 'destructive'}>{new Date(ch.expires_at) > new Date() ? 'Active' : 'Expired'}</Badge></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default WebAuthnPage;
