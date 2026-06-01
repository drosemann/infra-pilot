import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';

interface OIDCProvider {
  id: string;
  name: string;
  issuer_url: string;
  client_id: string;
  enabled: boolean;
}

interface SAMLProvider {
  id: string;
  name: string;
  entity_id: string;
  acs_url: string;
}

interface ClientRegistration {
  client_id: string;
  client_secret: string;
  name: string;
  redirect_uris: string[];
}

export const IdentityProvider = () => {
  const intl = useIntl();
  const navigate = useNavigate();
  const [oidcProviders, setOidcProviders] = useState<OIDCProvider[]>([]);
  const [samlProviders, setSamlProviders] = useState<SAMLProvider[]>([]);
  const [clients, setClients] = useState<ClientRegistration[]>([]);
  const [loading, setLoading] = useState(true);
  const [newProviderName, setNewProviderName] = useState('');
  const [newProviderIssuer, setNewProviderIssuer] = useState('');
  const [newProviderClientId, setNewProviderClientId] = useState('');
  const [newProviderClientSecret, setNewProviderClientSecret] = useState('');
  const [newClientName, setNewClientName] = useState('');
  const [newClientRedirectUri, setNewClientRedirectUri] = useState('');
  const [showProviderDialog, setShowProviderDialog] = useState(false);
  const [showClientDialog, setShowClientDialog] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [oidcData, samlData, clientsData] = await Promise.all([
        apiClient.listOidcProviders(),
        apiClient.listSamlProviders(),
        apiClient.listClients(),
      ]);
      setOidcProviders(oidcData || []);
      setSamlProviders(samlData || []);
      setClients(clientsData || []);
    } catch (error) {
      toast.error('Failed to load identity providers');
    } finally {
      setLoading(false);
    }
  };

  const createOidcProvider = async () => {
    try {
      const provider = await apiClient.createOidcProvider({
        name: newProviderName,
        issuer_url: newProviderIssuer,
        client_id: newProviderClientId,
        client_secret: newProviderClientSecret,
      });
      setOidcProviders([...oidcProviders, provider]);
      toast.success('OIDC provider created');
      setShowProviderDialog(false);
      setNewProviderName('');
      setNewProviderIssuer('');
      setNewProviderClientId('');
      setNewProviderClientSecret('');
    } catch (error) {
      toast.error('Failed to create provider');
    }
  };

  const registerClient = async () => {
    try {
      const client = await apiClient.registerClient({
        name: newClientName,
        redirect_uris: [newClientRedirectUri],
      });
      setClients([...clients, client]);
      toast.success('Client registered');
      setShowClientDialog(false);
      setNewClientName('');
      setNewClientRedirectUri('');
    } catch (error) {
      toast.error('Failed to register client');
    }
  };

  const deleteProvider = async (id: string) => {
    try {
      await apiClient.deleteOidcProvider(id);
      setOidcProviders(oidcProviders.filter((p) => p.id !== id));
      toast.success('Provider deleted');
    } catch (error) {
      toast.error('Failed to delete provider');
    }
  };

  const deleteClient = async (clientId: string) => {
    try {
      await apiClient.deleteClient(clientId);
      setClients(clients.filter((c) => c.client_id !== clientId));
      toast.success('Client deleted');
    } catch (error) {
      toast.error('Failed to delete client');
    }
  };

  const copySecret = (secret: string) => {
    navigator.clipboard.writeText(secret);
    toast.success('Secret copied');
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold"><FormattedMessage id="identityProvider.title" defaultMessage="Identity Provider" /></h1>
          <p className="text-muted-foreground mt-1"><FormattedMessage id="identityProvider.description" defaultMessage="Manage OIDC and SAML identity providers" /></p>
        </div>
      </div>

      <Tabs defaultValue="oidc">
        <TabsList>
          <TabsTrigger value="oidc"><FormattedMessage id="identityProvider.oidc" defaultMessage="OIDC Providers" /></TabsTrigger>
          <TabsTrigger value="saml"><FormattedMessage id="identityProvider.saml" defaultMessage="SAML Providers" /></TabsTrigger>
          <TabsTrigger value="clients"><FormattedMessage id="identityProvider.clients" defaultMessage="Registered Clients" /></TabsTrigger>
        </TabsList>

        <TabsContent value="oidc" className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold"><FormattedMessage id="identityProvider.oidcProviders" defaultMessage="OIDC Providers" /></h2>
            <Dialog open={showProviderDialog} onOpenChange={setShowProviderDialog}>
              <DialogTrigger asChild>
                <Button><FormattedMessage id="identityProvider.addProvider" defaultMessage="Add Provider" /></Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle><FormattedMessage id="identityProvider.createOidc" defaultMessage="Create OIDC Provider" /></DialogTitle>
                  <DialogDescription><FormattedMessage id="identityProvider.createOidcDesc" defaultMessage="Configure a new OpenID Connect provider" /></DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <Label><FormattedMessage id="identityProvider.providerName" defaultMessage="Provider Name" /></Label>
                    <Input value={newProviderName} onChange={(e) => setNewProviderName(e.target.value)} placeholder="Azure AD" />
                  </div>
                  <div>
                    <Label><FormattedMessage id="identityProvider.issuerUrl" defaultMessage="Issuer URL" /></Label>
                    <Input value={newProviderIssuer} onChange={(e) => setNewProviderIssuer(e.target.value)} placeholder="https://login.microsoftonline.com/tenant/v2.0" />
                  </div>
                  <div>
                    <Label><FormattedMessage id="identityProvider.clientId" defaultMessage="Client ID" /></Label>
                    <Input value={newProviderClientId} onChange={(e) => setNewProviderClientId(e.target.value)} />
                  </div>
                  <div>
                    <Label><FormattedMessage id="identityProvider.clientSecret" defaultMessage="Client Secret" /></Label>
                    <Input type="password" value={newProviderClientSecret} onChange={(e) => setNewProviderClientSecret(e.target.value)} />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setShowProviderDialog(false)}><FormattedMessage id="common.cancel" defaultMessage="Cancel" /></Button>
                  <Button onClick={createOidcProvider}><FormattedMessage id="common.create" defaultMessage="Create" /></Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead><FormattedMessage id="common.name" defaultMessage="Name" /></TableHead>
                    <TableHead><FormattedMessage id="identityProvider.issuer" defaultMessage="Issuer" /></TableHead>
                    <TableHead><FormattedMessage id="identityProvider.clientId" defaultMessage="Client ID" /></TableHead>
                    <TableHead><FormattedMessage id="common.status" defaultMessage="Status" /></TableHead>
                    <TableHead><FormattedMessage id="common.actions" defaultMessage="Actions" /></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {oidcProviders.map((provider) => (
                    <TableRow key={provider.id}>
                      <TableCell className="font-medium">{provider.name}</TableCell>
                      <TableCell className="max-w-[200px] truncate">{provider.issuer_url}</TableCell>
                      <TableCell className="font-mono text-sm">{provider.client_id}</TableCell>
                      <TableCell><Badge variant={provider.enabled ? "default" : "secondary"}>{provider.enabled ? 'Enabled' : 'Disabled'}</Badge></TableCell>
                      <TableCell>
                        <Button variant="destructive" size="sm" onClick={() => deleteProvider(provider.id)}><FormattedMessage id="common.delete" defaultMessage="Delete" /></Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="saml" className="space-y-4">
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead><FormattedMessage id="common.name" defaultMessage="Name" /></TableHead>
                    <TableHead><FormattedMessage id="identityProvider.entityId" defaultMessage="Entity ID" /></TableHead>
                    <TableHead><FormattedMessage id="identityProvider.acsUrl" defaultMessage="ACS URL" /></TableHead>
                    <TableHead><FormattedMessage id="common.actions" defaultMessage="Actions" /></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {samlProviders.map((provider) => (
                    <TableRow key={provider.id}>
                      <TableCell className="font-medium">{provider.name}</TableCell>
                      <TableCell className="font-mono text-sm">{provider.entity_id}</TableCell>
                      <TableCell className="max-w-[200px] truncate">{provider.acs_url}</TableCell>
                      <TableCell><Button variant="destructive" size="sm"><FormattedMessage id="common.delete" defaultMessage="Delete" /></Button></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="clients" className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold"><FormattedMessage id="identityProvider.registeredClients" defaultMessage="Registered Clients" /></h2>
            <Dialog open={showClientDialog} onOpenChange={setShowClientDialog}>
              <DialogTrigger asChild>
                <Button><FormattedMessage id="identityProvider.registerClient" defaultMessage="Register Client" /></Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle><FormattedMessage id="identityProvider.registerNewClient" defaultMessage="Register New Client" /></DialogTitle>
                  <DialogDescription><FormattedMessage id="identityProvider.registerClientDesc" defaultMessage="Register a new OAuth2 client application" /></DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <Label><FormattedMessage id="common.name" defaultMessage="Name" /></Label>
                    <Input value={newClientName} onChange={(e) => setNewClientName(e.target.value)} placeholder="My App" />
                  </div>
                  <div>
                    <Label><FormattedMessage id="identityProvider.redirectUri" defaultMessage="Redirect URI" /></Label>
                    <Input value={newClientRedirectUri} onChange={(e) => setNewClientRedirectUri(e.target.value)} placeholder="https://app.example.com/callback" />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setShowClientDialog(false)}><FormattedMessage id="common.cancel" defaultMessage="Cancel" /></Button>
                  <Button onClick={registerClient}><FormattedMessage id="identityProvider.register" defaultMessage="Register" /></Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead><FormattedMessage id="common.name" defaultMessage="Name" /></TableHead>
                    <TableHead><FormattedMessage id="identityProvider.clientId" defaultMessage="Client ID" /></TableHead>
                    <TableHead><FormattedMessage id="identityProvider.clientSecret" defaultMessage="Client Secret" /></TableHead>
                    <TableHead><FormattedMessage id="identityProvider.redirectUris" defaultMessage="Redirect URIs" /></TableHead>
                    <TableHead><FormattedMessage id="common.actions" defaultMessage="Actions" /></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {clients.map((client) => (
                    <TableRow key={client.client_id}>
                      <TableCell className="font-medium">{client.name}</TableCell>
                      <TableCell className="font-mono text-xs">{client.client_id.substring(0, 12)}...</TableCell>
                      <TableCell>
                        <Button variant="ghost" size="sm" onClick={() => copySecret(client.client_secret)}>
                          <FormattedMessage id="identityProvider.copy" defaultMessage="Copy" />
                        </Button>
                      </TableCell>
                      <TableCell className="max-w-[150px] truncate">{client.redirect_uris.join(', ')}</TableCell>
                      <TableCell><Button variant="destructive" size="sm" onClick={() => deleteClient(client.client_id)}><FormattedMessage id="common.delete" defaultMessage="Delete" /></Button></TableCell>
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

export default IdentityProvider;
