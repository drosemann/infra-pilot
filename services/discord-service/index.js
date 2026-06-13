const { Client, GatewayIntentBits, Partials, EmbedBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle } = require('discord.js');
const axios = require('axios');
const dotenv = require('dotenv');
const fs = require('fs');
const path = require('path');

dotenv.config();

// --- Constants and Configuration ---
const SERVER_LIMITS_FILE = path.join(__dirname, 'server_limits.json');
const DISCORD_TOKEN = process.env.DISCORD_TOKEN;
const PTERODACTYL_API_URL = process.env.PTERODACTYL_API_URL;
const PTERODACTYL_API_KEY = process.env.PTERODACTYL_API_KEY;
const SERVER_CREATION_CHANNEL_ID = process.env.SERVER_CREATION_CHANNEL_ID;
const SERVER_CREATOR_ROLE_ID = process.env.SERVER_CREATOR_ROLE_ID;
const LOCATION_ID = process.env.LOCATION_ID;
const MAX_SERVERS_PER_USER = parseInt(process.env.MAX_SERVERS_PER_USER) || 1;
const DISCORD_SERVICE_DISABLED = String(process.env.DISCORD_SERVICE_DISABLED || '').toLowerCase() === 'true';

// --- Server Types Configuration ---
const SERVER_TYPES = {
  'minecraft': {
    name: 'Minecraft Server',
    eggId: process.env.MINECRAFT_EGG_ID,
    memory: 1024,
    dockerImage: 'ghcr.io/pterodactyl/yolks:java_17'
  },
  'nodejs': {
    name: 'Node.js Server',
    eggId: process.env.NODEJS_EGG_ID,
    memory: 256,
    dockerImage: 'ghcr.io/pterodactyl/yolks:nodejs_18'
  },
  'teamspeak': {
    name: 'TeamSpeak Server',
    eggId: process.env.TEAMSPEAK_EGG_ID,
    memory: 256,
    dockerImage: 'ghcr.io/pterodactyl/yolks:teamspeak'
  },
  'database': {
    name: 'MySQL Datenbank',
    eggId: process.env.DATABASE_EGG_ID,
    memory: 256,
    dockerImage: 'ghcr.io/pterodactyl/yolks:mysql'
  },
  'python': {
    name: 'Python Server',
    eggId: process.env.PYTHON_EGG_ID,
    memory: 512,
    dockerImage: 'ghcr.io/pterodactyl/yolks:python_3.10'
  }
};

// --- Load Existing Modules ---
const ServerStatus = require('./modules/serverStatus');
const TicketSystem = require('./modules/ticketSystem');
const TicketCommands = require('./modules/ticketCommands');
const StatsCommands = require('./modules/statsCommands');
const RoleManager = require('./modules/roleManager');
const TopicRotation = require('./modules/topicRotation');
const StatsGraphs = require('./modules/statsGraphs');
const VerificationLevels = require('./modules/verificationLevels');
const CodeReviewBot = require('./modules/codeReviewBot');
const ReportBot = require('./modules/reportBot');

// --- Utility Functions ---
function loadServerLimits() {
  try {
    if (!fs.existsSync(SERVER_LIMITS_FILE)) {
      fs.writeFileSync(SERVER_LIMITS_FILE, JSON.stringify({}));
    }
    return JSON.parse(fs.readFileSync(SERVER_LIMITS_FILE, 'utf8'));
  } catch (error) {
    console.error('Fehler beim Laden der Serverlimits:', error);
    return {};
  }
}

function saveServerLimits(limits) {
  try {
    fs.writeFileSync(SERVER_LIMITS_FILE, JSON.stringify(limits, null, 2));
  } catch (error) {
    console.error('Fehler beim Speichern der Serverlimits:', error);
  }
}

async function createPterodactylUser(userData) {
  try {
    const response = await axios.post(`${PTERODACTYL_API_URL}/api/application/users`, userData, {
      headers: {
        'Authorization': `Bearer ${PTERODACTYL_API_KEY}`,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    });
    return response.data.attributes;
  } catch (error) {
    console.error('API Error creating user:', error.response?.data || error.message);
    throw new Error(error.response?.data?.errors?.[0]?.detail || 'Failed to create user');
  }
}

async function createPterodactylServer(serverData) {
  try {
    const response = await axios.post(`${PTERODACTYL_API_URL}/api/application/servers`, serverData, {
      headers: {
        'Authorization': `Bearer ${PTERODACTYL_API_KEY}`,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    });
    return response.data.attributes;
  } catch (error) {
    console.error('API Error creating server:', error.response?.data || error.message);
    throw new Error(error.response?.data?.errors?.[0]?.detail || 'Failed to create server');
  }
}

function validateEmail(email) {
  const re = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
  return re.test(String(email).toLowerCase());
}

function validateUsername(username) {
  const re = /^[a-zA-Z0-9_]{3,20}$/;
  return re.test(username);
}

function validatePassword(password) {
  return password.length >= 8 &&
    /[A-Za-z]/.test(password) &&
    /[0-9]/.test(password) &&
    /[^A-Za-z0-9]/.test(password);
}

// --- Discord Client Initialization ---
const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
    GatewayIntentBits.GuildMembers,
    GatewayIntentBits.GuildMessageReactions,
    GatewayIntentBits.MessageContent,
    GatewayIntentBits.GuildVoiceStates,
    GatewayIntentBits.GuildModeration,
    GatewayIntentBits.GuildIntegrations,
  ],
  partials: [Partials.Channel, Partials.Message, Partials.Reaction, Partials.User],
});

// --- State Management ---
const userRegistrationState = new Map();

// --- Instantiate All Modules ---
const ticketSystem = new TicketSystem(client);
const ticketCommands = new TicketCommands(ticketSystem);
const statsCommands = new StatsCommands(client);
const roleManager = new RoleManager(client);
const economyCommands = new EconomyCommands(client);
const dashboard = new DashboardManager(client);

const advancedTicketSystem = new AdvancedTicketSystem(client, ticketSystem);
const serverStatus = new ServerStatus(client);
const eventScheduler = new EventScheduler(client);
const pollCreator = new PollCreator(client);
const roleHierarchy = new RoleHierarchy(client, roleManager);
const customCommands = new CustomCommands(client);
const prefixSettings = new PrefixSettings(client);
const warningSystem = new WarningSystem(client);
const verificationSystem = new VerificationSystem(client);
const messageFilter = new MessageFilter(client);
const messageLogger = new MessageLogger(client);
const activityTracker = new ActivityTracker(client);
const welcomeMessages = new WelcomeMessages(client);
const voiceManager = new VoiceManager(client);
const tempVoiceChannels = new TempVoiceChannels(client);
const messageScheduler = new MessageScheduler(client);
const channelCleanup = new ChannelCleanup(client);
const messageArchive = new MessageArchive(client);
const categoryManager = new CategoryManager(client);
const topicRotation = new TopicRotation(client);
const statsGraphs = new StatsGraphs(client);
const verificationLevels = new VerificationLevels(client);
const codeReviewBot = new CodeReviewBot(client);
const reportBot = new ReportBot(client);

// --- Helper Functions for Message Handling ---
async function handleEmailInput(message, userState) {
  if (!validateEmail(message.content)) {
    await message.reply({
      content: 'Ungültige E-Mail-Adresse. Bitte gib eine gültige E-Mail-Adresse ein.',
      ephemeral: true
    });
    return false;
  }

  userState.data.email = message.content;
  userState.step = 'username';

  const usernameEmbed = new EmbedBuilder()
    .setTitle('Server-Erstellung')
    .setDescription('E-Mail gespeichert. Bitte gib nun deinen gewünschten Benutzernamen ein:')
    .setColor('#007bff')
    .setFooter({ text: 'Schritt 2 von 3: Benutzername' });

  await message.reply({ embeds: [usernameEmbed], ephemeral: true });
  return true;
}

async function handleUsernameInput(message, userState) {
  if (!validateUsername(message.content)) {
    await message.reply({
      content: 'Ungültiger Benutzername. Der Benutzername muss 3-20 Zeichen lang sein und darf nur Buchstaben, Zahlen und Unterstriche enthalten.',
      ephemeral: true
    });
    return false;
  }

  userState.data.username = message.content;
  userState.step = 'password';

  const passwordEmbed = new EmbedBuilder()
    .setTitle('Server-Erstellung')
    .setDescription('Benutzername gespeichert. Bitte gib nun dein gewünschtes Passwort ein.\n\n**Sicherheitshinweis**: Dein Passwort sollte mindestens 8 Zeichen lang sein und eine Kombination aus Buchstaben, Zahlen und Sonderzeichen enthalten.')
    .setColor('#007bff')
    .setFooter({ text: 'Schritt 3 von 3: Passwort' });

  await message.reply({ embeds: [passwordEmbed], ephemeral: true });
  return true;
}

async function handlePasswordInput(message, userState) {
  if (!validatePassword(message.content)) {
    await message.reply({
      content: 'Passwort zu schwach. Es sollte mindestens 8 Zeichen lang sein und Buchstaben, Zahlen und Sonderzeichen enthalten.',
      ephemeral: true
    });
    return false;
  }

  userState.data.password = message.content;
  userState.step = 'processing';

  const processingEmbed = new EmbedBuilder()
    .setTitle('Server-Erstellung')
    .setDescription('Alle Informationen gesammelt. Erstelle deinen Account und Server...')
    .setColor('#ffc107')
    .setFooter({ text: 'Wird verarbeitet...' });

  const processingMsg = await message.reply({ embeds: [processingEmbed], ephemeral: true });
  return { processingMsg };
}

async function processServerCreation(message, userState, processingMsg) {
  try {
    const userData = {
      username: userState.data.username,
      email: userState.data.email,
      first_name: userState.data.username,
      last_name: 'User',
      password: userState.data.password,
      root_admin: false,
      language: 'en'
    };

    const userResponse = await createPterodactylUser(userData);
    const userId = userResponse.id;

    const serverType = userState.data.serverType;
    const serverConfig = SERVER_TYPES[serverType];

    const serverData = {
      name: `${userState.data.username}'s ${serverConfig.name}`,
      user: userId,
      egg: parseInt(serverConfig.eggId),
      docker_image: serverConfig.dockerImage,
      startup: serverType === 'nodejs' ? 'npm start' : '',
      environment: serverType === 'nodejs'
        ? {
          STARTUP_CMD: 'npm start',
          NODE_VERSION: '18'
        }
        : {},
      limits: {
        memory: serverConfig.memory,
        swap: 0,
        disk: 1024,
        io: 500,
        cpu: 100
      },
      feature_limits: {
        databases: 0,
        allocations: 1,
        backups: 1
      },
      allocation: {
        default: null
      },
      deploy: {
        locations: [parseInt(LOCATION_ID)],
        dedicated_ip: false,
        port_range: []
      }
    };

    const serverResponse = await createPterodactylServer(serverData);

    const serverLimits = loadServerLimits();
    const userServers = serverLimits[message.author.id] || [];
    userServers.push(serverResponse.identifier);
    serverLimits[message.author.id] = userServers;
    saveServerLimits(serverLimits);

    try {
      const member = await message.guild.members.fetch(message.author.id);
      await member.roles.add(SERVER_CREATOR_ROLE_ID);
    } catch (roleError) {
      console.error('Fehler beim Zuweisen der Rolle:', roleError);
    }

    const successEmbed = new EmbedBuilder()
      .setTitle('✅ Server-Erstellung erfolgreich')
      .setDescription(`Glückwunsch! Dein ${serverConfig.name} wurde erfolgreich erstellt.

**Serverdetails:**
- Name: ${serverResponse.name}
- Typ: ${serverConfig.name}
- Speicher: ${serverConfig.memory} MB
- Server-ID: ${serverResponse.identifier}

Du kannst dich nun mit deiner E-Mail und dem Passwort im Pterodactyl-Panel anmelden.`)
      .setColor('#28a745')
      .setFooter({ text: 'Einrichtung abgeschlossen' });

    await processingMsg.edit({ embeds: [successEmbed] });
  } catch (error) {
    console.error('Fehler bei der Server-Erstellung:', error);

    const errorEmbed = new EmbedBuilder()
      .setTitle('❌ Server-Erstellung fehlgeschlagen')
      .setDescription(`Es gab einen Fehler bei der Erstellung deines Accounts oder Servers: ${error.message || 'Unbekannter Fehler'}

Bitte versuche es später erneut oder kontaktiere einen Administrator.`)
      .setColor('#dc3545')
      .setFooter({ text: 'Fehler' });

    await processingMsg.edit({ embeds: [errorEmbed] });
  } finally {
    userRegistrationState.delete(message.author.id);
  }
}

// --- Command Registration Helper ---
async function registerCommands() {
  const allCommands = [
    {
      name: 'server',
      description: 'Server-Verwaltungsbefehle',
      options: [
        {
          name: 'create',
          description: 'Erstelle einen neuen Server',
          type: 1,
        }
      ]
    },
    {
      name: 'setuptickets',
      description: 'Set up the ticket system in the current channel',
      type: 1
    },
    {
      name: 'addstaff',
      description: 'Add a staff member to the current ticket',
      type: 1,
      options: [
        { name: 'user', description: 'The staff member to add', type: 6, required: true }
      ]
    },
    {
      name: 'removestaff',
      description: 'Remove a staff member from the current ticket',
      type: 1,
      options: [
        { name: 'user', description: 'The staff member to remove', type: 6, required: true }
      ]
    },
    {
      name: 'ticketstats',
      description: 'View ticket statistics',
      type: 1
    },
    {
      name: 'serverstats',
      description: 'View your Minecraft server statistics',
      type: 1,
      options: [
        { name: 'player', description: 'Player to check stats for (staff only)', type: 6, required: false }
      ]
    },
    {
      name: 'leaderboard',
      description: 'View server statistics leaderboard',
      type: 1,
      options: [
        { name: 'category', description: 'Leaderboard category', type: 3, required: true,
          choices: [
            { name: 'Players', value: 'players' },
            { name: 'Uptime', value: 'uptime' },
            { name: 'Playtime', value: 'playtime' }
          ]
        }
      ]
    },
    {
      name: 'balance',
      description: 'Check your balance',
      type: 1,
      options: [
        { name: 'user', description: 'User to check balance for (staff only)', type: 6, required: false }
      ]
    },
    {
      name: 'pay',
      description: 'Pay another user',
      type: 1,
      options: [
        { name: 'user', description: 'User to pay', type: 6, required: true },
        { name: 'amount', description: 'Amount to pay', type: 10, required: true }
      ]
    },
    {
      name: 'baltop',
      description: 'View top balances',
      type: 1
    },
    {
      name: 'ecoadmin',
      description: 'Manage user balances (Admin only)',
      type: 1,
      options: [
        { name: 'give', description: 'Give money to a user', type: 1,
          options: [
            { name: 'user', description: 'User to give money to', type: 6, required: true },
            { name: 'amount', description: 'Amount to give', type: 10, required: true }
          ]
        },
        { name: 'take', description: 'Take money from a user', type: 1,
          options: [
            { name: 'user', description: 'User to take money from', type: 6, required: true },
            { name: 'amount', description: 'Amount to take', type: 10, required: true }
          ]
        }
      ]
    },
    {
      name: 'dashboard',
      description: 'Create a system dashboard',
      type: 1
    },
    {
      name: 'ticket',
      description: 'Advanced ticket system commands',
      type: 1,
      options: [
        { name: 'panel', description: 'Create a ticket panel with categories', type: 1 },
        { name: 'priority', description: 'Set ticket priority', type: 1,
          options: [
            { name: 'level', description: 'Priority level', type: 3, required: true,
              choices: [
                { name: 'Low', value: 'low' },
                { name: 'Medium', value: 'medium' },
                { name: 'High', value: 'high' },
                { name: 'Critical', value: 'critical' }
              ]
            }
          ]
        },
        { name: 'close', description: 'Close the current ticket with rating', type: 1 }
      ]
    },
    {
      name: 'status',
      description: 'Server status commands',
      type: 1,
      options: [
        { name: 'widget', description: 'Create a status widget', type: 1 },
        { name: 'info', description: 'Show live server status', type: 1 }
      ]
    },
    {
      name: 'event',
      description: 'Event scheduling commands',
      type: 1,
      options: [
        { name: 'create', description: 'Create a new event', type: 1,
          options: [
            { name: 'name', description: 'Event name', type: 3, required: true },
            { name: 'description', description: 'Event description', type: 3, required: true },
            { name: 'time', description: 'Event time (ISO format or "in 2h")', type: 3, required: true },
            { name: 'recurring', description: 'Recurring interval (daily/weekly/monthly)', type: 3, required: false,
              choices: [
                { name: 'None', value: 'none' },
                { name: 'Daily', value: 'daily' },
                { name: 'Weekly', value: 'weekly' },
                { name: 'Monthly', value: 'monthly' }
              ]
            },
            { name: 'role', description: 'Role to ping', type: 8, required: false }
          ]
        },
        { name: 'list', description: 'List upcoming events', type: 1 },
        { name: 'remind', description: 'Set a reminder for an event', type: 1,
          options: [
            { name: 'id', description: 'Event ID', type: 3, required: true },
            { name: 'time', description: 'Reminder time before event (e.g. 30m, 1h)', type: 3, required: true }
          ]
        }
      ]
    },
    {
      name: 'poll',
      description: 'Server poll commands',
      type: 1,
      options: [
        { name: 'create', description: 'Create a poll', type: 1,
          options: [
            { name: 'question', description: 'Poll question', type: 3, required: true },
            { name: 'option1', description: 'Option 1', type: 3, required: true },
            { name: 'option2', description: 'Option 2', type: 3, required: true },
            { name: 'option3', description: 'Option 3', type: 3, required: false },
            { name: 'option4', description: 'Option 4', type: 3, required: false },
            { name: 'option5', description: 'Option 5', type: 3, required: false },
            { name: 'duration', description: 'Duration in minutes', type: 4, required: false },
            { name: 'anonymous', description: 'Anonymous poll', type: 5, required: false }
          ]
        },
        { name: 'vote', description: 'Vote on a poll', type: 1,
          options: [
            { name: 'message_id', description: 'Poll message ID', type: 3, required: true },
            { name: 'option', description: 'Option number (1-5)', type: 4, required: true }
          ]
        },
        { name: 'results', description: 'Show poll results', type: 1,
          options: [
            { name: 'message_id', description: 'Poll message ID', type: 3, required: true }
          ]
        }
      ]
    },
    {
      name: 'role',
      description: 'Role management commands',
      type: 1,
      options: [
        { name: 'create', description: 'Create a new role', type: 1,
          options: [
            { name: 'name', description: 'Role name', type: 3, required: true },
            { name: 'color', description: 'Role color (hex)', type: 3, required: false },
            { name: 'hoist', description: 'Display role separately', type: 5, required: false }
          ]
        },
        { name: 'delete', description: 'Delete a role', type: 1,
          options: [
            { name: 'role', description: 'Role to delete', type: 8, required: true }
          ]
        },
        { name: 'edit', description: 'Edit a role', type: 1,
          options: [
            { name: 'role', description: 'Role to edit', type: 8, required: true },
            { name: 'name', description: 'New name', type: 3, required: false },
            { name: 'color', description: 'New color (hex)', type: 3, required: false }
          ]
        },
        { name: 'info', description: 'Show role hierarchy info', type: 1 },
        { name: 'menu', description: 'Create a reaction role menu', type: 1,
          options: [
            { name: 'channel', description: 'Target channel', type: 7, required: true }
          ]
        }
      ]
    },
    {
      name: 'command',
      description: 'Custom command management',
      type: 1,
      options: [
        { name: 'create', description: 'Create a custom command', type: 1,
          options: [
            { name: 'name', description: 'Command name', type: 3, required: true },
            { name: 'response', description: 'Response text', type: 3, required: true },
            { name: 'embed_title', description: 'Embed title (optional)', type: 3, required: false },
            { name: 'embed_color', description: 'Embed color (hex)', type: 3, required: false }
          ]
        },
        { name: 'delete', description: 'Delete a custom command', type: 1,
          options: [
            { name: 'name', description: 'Command name', type: 3, required: true }
          ]
        },
        { name: 'list', description: 'List all custom commands', type: 1 }
      ]
    },
    {
      name: 'prefix',
      description: 'Custom prefix commands',
      type: 1,
      options: [
        { name: 'set', description: 'Set a custom prefix', type: 1,
          options: [
            { name: 'prefix', description: 'New prefix', type: 3, required: true }
          ]
        },
        { name: 'reset', description: 'Reset to default prefix', type: 1 }
      ]
    },
    {
      name: 'warn',
      description: 'Warn a user',
      type: 1,
      options: [
        { name: 'user', description: 'User to warn', type: 6, required: true },
        { name: 'reason', description: 'Warning reason', type: 3, required: true }
      ]
    },
    {
      name: 'warnings',
      description: 'View warnings for a user',
      type: 1,
      options: [
        { name: 'user', description: 'User to check', type: 6, required: false }
      ]
    },
    {
      name: 'warnremove',
      description: 'Remove a warning',
      type: 1,
      options: [
        { name: 'user', description: 'User', type: 6, required: true },
        { name: 'warning_id', description: 'Warning ID', type: 3, required: true }
      ]
    },
    {
      name: 'verify',
      description: 'Verification system',
      type: 1,
      options: [
        { name: 'config', description: 'Configure verification', type: 1,
          options: [
            { name: 'channel', description: 'Verification channel', type: 7, required: true },
            { name: 'role', description: 'Verified role', type: 8, required: true }
          ]
        }
      ]
    },
    {
      name: 'filter',
      description: 'Message filter configuration',
      type: 1,
      options: [
        { name: 'config', description: 'Configure message filter', type: 1,
          options: [
            { name: 'action', description: 'Action to take on filtered content', type: 3, required: true,
              choices: [
                { name: 'Delete', value: 'delete' },
                { name: 'Warn', value: 'warn' },
                { name: 'Timeout', value: 'timeout' }
              ]
            },
            { name: 'log_channel', description: 'Log channel for filter actions', type: 7, required: false }
          ]
        },
        { name: 'badword', description: 'Add a bad word to filter', type: 1,
          options: [
            { name: 'word', description: 'Word to filter', type: 3, required: true }
          ]
        },
        { name: 'badword_remove', description: 'Remove a bad word from filter', type: 1,
          options: [
            { name: 'word', description: 'Word to remove', type: 3, required: true }
          ]
        },
        { name: 'whitelist', description: 'Whitelist a domain', type: 1,
          options: [
            { name: 'domain', description: 'Domain to whitelist', type: 3, required: true }
          ]
        }
      ]
    },
    {
      name: 'activity',
      description: 'Activity tracking',
      type: 1,
      options: [
        { name: 'leaderboard', description: 'Show activity leaderboard', type: 1 },
        { name: 'stats', description: 'Show your activity stats', type: 1 }
      ]
    },
    {
      name: 'welcome',
      description: 'Welcome message configuration',
      type: 1,
      options: [
        { name: 'set', description: 'Set welcome message', type: 1,
          options: [
            { name: 'channel', description: 'Welcome channel', type: 7, required: true },
            { name: 'message', description: 'Welcome message text', type: 3, required: true },
            { name: 'dm', description: 'Send welcome via DM too', type: 5, required: false }
          ]
        },
        { name: 'preview', description: 'Preview welcome message', type: 1 }
      ]
    },
    {
      name: 'voice',
      description: 'Voice channel management',
      type: 1,
      options: [
        { name: 'create', description: 'Create a temporary voice channel', type: 1,
          options: [
            { name: 'name', description: 'Channel name', type: 3, required: true },
            { name: 'limit', description: 'User limit', type: 4, required: false }
          ]
        },
        { name: 'limit', description: 'Set voice channel user limit', type: 1,
          options: [
            { name: 'limit', description: 'User limit', type: 4, required: true }
          ]
        },
        { name: 'lock', description: 'Lock your voice channel', type: 1 },
        { name: 'unlock', description: 'Unlock your voice channel', type: 1 },
        { name: 'claim', description: 'Claim voice channel ownership', type: 1 }
      ]
    },
    {
      name: 'schedule',
      description: 'Message scheduling',
      type: 1,
      options: [
        { name: 'message', description: 'Schedule a message', type: 1,
          options: [
            { name: 'channel', description: 'Target channel', type: 7, required: true },
            { name: 'content', description: 'Message content', type: 3, required: true },
            { name: 'time', description: 'Time (ISO format or "in 30m")', type: 3, required: true },
            { name: 'recurring', description: 'Recurring (cron expression)', type: 3, required: false }
          ]
        }
      ]
    },
    {
      name: 'purge',
      description: 'Channel cleanup',
      type: 1,
      options: [
        { name: 'all', description: 'Purge all messages', type: 1,
          options: [
            { name: 'count', description: 'Number of messages (max 100)', type: 4, required: true }
          ]
        },
        { name: 'user', description: 'Purge messages from a user', type: 1,
          options: [
            { name: 'user', description: 'Target user', type: 6, required: true },
            { name: 'count', description: 'Number of messages (max 100)', type: 4, required: true }
          ]
        },
        { name: 'bot', description: 'Purge bot messages', type: 1,
          options: [
            { name: 'count', description: 'Number of messages (max 100)', type: 4, required: true }
          ]
        }
      ]
    },
    {
      name: 'archive',
      description: 'Message archival',
      type: 1,
      options: [
        { name: 'channel', description: 'Archive a channel', type: 1,
          options: [
            { name: 'channel', description: 'Channel to archive', type: 7, required: true },
            { name: 'format', description: 'Export format', type: 3, required: false,
              choices: [
                { name: 'JSON', value: 'json' },
                { name: 'CSV', value: 'csv' },
                { name: 'TXT', value: 'txt' }
              ]
            }
          ]
        }
      ]
    },
    {
      name: 'category',
      description: 'Channel category management',
      type: 1,
      options: [
        { name: 'create', description: 'Create a new category', type: 1,
          options: [
            { name: 'name', description: 'Category name', type: 3, required: true }
          ]
        },
        { name: 'add', description: 'Add a channel to a category', type: 1,
          options: [
            { name: 'channel', description: 'Channel to add', type: 7, required: true },
            { name: 'category', description: 'Target category', type: 7, required: true }
          ]
        },
        { name: 'permissions', description: 'Sync category permissions', type: 1,
          options: [
            { name: 'category', description: 'Category to sync', type: 7, required: true }
          ]
        }
      ]
    },
    {
      name: 'statsgraph',
      description: 'View server statistics graphs',
      type: 1,
      options: [
        {
          name: 'members',
          description: 'Show member growth chart (30 days)',
          type: 1
        },
        {
          name: 'messages',
          description: 'Show message volume chart',
          type: 1,
          options: [
            { name: 'channel', description: 'Channel to analyze', type: 7, required: false }
          ]
        }
      ]
    },
    {
      name: 'verifylevel',
      description: 'User verification levels',
      type: 1,
      options: [
        { name: 'config', description: 'Configure verification levels', type: 1,
          options: [
            { name: 'required_age_days', description: 'Required account age in days', type: 4, required: false },
            { name: 'required_guild_days', description: 'Required days in server', type: 4, required: false },
            { name: 'required_role', description: 'Required role', type: 8, required: false }
          ]
        }
      ]
    },
    {
      name: 'codereview',
      description: 'AI Code Review commands',
      type: 1,
      options: [
        { name: 'config', description: 'View code review configuration', type: 1 },
        { name: 'history', description: 'View recent code review history', type: 1 },
        { name: 'enable', description: 'Enable code review for this server', type: 1 },
        { name: 'disable', description: 'Disable code review for this server', type: 1 }
      ]
    },
    {
      name: 'report',
      description: 'Report bot commands',
      type: 1,
      options: [
        { name: 'send', description: 'Send a report to this channel', type: 1,
          options: [
            { name: 'type', description: 'Report type', type: 3, required: false,
              choices: [
                { name: 'Executive Summary', value: 'executive-summary' },
                { name: 'Cost Report', value: 'cost' },
                { name: 'Performance Report', value: 'performance' },
                { name: 'Incident Report', value: 'incidents' },
                { name: 'Anomaly Digest', value: 'anomaly-digest' },
                { name: 'Capacity Forecast', value: 'capacity-forecast' }
              ]
            },
            { name: 'period', description: 'Time period', type: 3, required: false,
              choices: [
                { name: '1 hour', value: '1h' },
                { name: '24 hours', value: '24h' },
                { name: '7 days', value: '7d' },
                { name: '30 days', value: '30d' }
              ]
            }
          ]
        },
        { name: 'digest', description: 'Send infrastructure digest', type: 1,
          options: [
            { name: 'mode', description: 'Digest mode', type: 3, required: false,
              choices: [
                { name: 'Daily', value: 'daily' },
                { name: 'Weekly', value: 'weekly' },
                { name: 'Monthly', value: 'monthly' }
              ]
            }
          ]
        },
        { name: 'schedule', description: 'Schedule a recurring report', type: 1,
          options: [
            { name: 'name', description: 'Schedule name', type: 3, required: true },
            { name: 'type', description: 'Report type', type: 3, required: false,
              choices: [
                { name: 'Executive Summary', value: 'executive-summary' },
                { name: 'Cost Report', value: 'cost' },
                { name: 'Performance Report', value: 'performance' },
                { name: 'Incident Report', value: 'incidents' },
                { name: 'Anomaly Digest', value: 'anomaly-digest' },
                { name: 'Capacity Forecast', value: 'capacity-forecast' }
              ]
            },
            { name: 'cron', description: 'Cron expression', type: 3, required: false },
            { name: 'channel', description: 'Target channel', type: 7, required: false }
          ]
        },
        { name: 'list', description: 'List report schedules', type: 1 },
        { name: 'delete', description: 'Delete a report schedule', type: 1,
          options: [
            { name: 'id', description: 'Schedule ID', type: 3, required: true }
          ]
        }
      ]
    }
  ];

  try {
    for (const cmd of allCommands) {
      await client.application.commands.create(cmd);
    }
    console.log(`[Commands] ${allCommands.length} slash commands registered.`);
  } catch (error) {
    console.error('[Commands] Error registering commands:', error);
  }
}

// --- Event Handlers ---
client.once('ready', async () => {
  console.log(`Bot ist online als ${client.user.tag}`);
  await registerCommands();

  welcomeMessages.initialize(client);
  messageScheduler.initialize(client);
  topicRotation.initialize(client);
  tempVoiceChannels.initialize(client);
  messageLogger.initialize(client);
  activityTracker.initialize(client);
  verificationSystem.initialize(client);
  serverStatus.initialize(client);
  eventScheduler.initialize(client);
  reportBot.initialize(client);
});

client.on('guildMemberAdd', async (member) => {
  welcomeMessages.handleMemberJoin(member);
  verificationSystem.handleMemberJoin(member);
  verificationLevels.checkMember(member);
});

client.on('guildMemberRemove', async (member) => {
  tempVoiceChannels.handleMemberLeave(member);
});

client.on('messageDelete', async (message) => {
  messageLogger.handleMessageDelete(message);
});

client.on('messageUpdate', async (oldMessage, newMessage) => {
  messageFilter.handleMessageUpdate(oldMessage, newMessage);
});

client.on('interactionCreate', async (interaction) => {
  if (interaction.isCommand()) {
    if (interaction.channelId === SERVER_CREATION_CHANNEL_ID && interaction.commandName === 'server') {
      const serverLimits = loadServerLimits();
      const userServers = serverLimits[interaction.user.id] || [];

      if (userServers.length >= MAX_SERVERS_PER_USER) {
        return interaction.reply({
          content: `Du hast bereits die maximale Anzahl von ${MAX_SERVERS_PER_USER} Servern erreicht.`,
          ephemeral: true
        });
      }

      const row = new ActionRowBuilder()
        .addComponents(
          Object.entries(SERVER_TYPES).filter(([key, type]) => key !== 'debian').map(([key, type]) =>
            new ButtonBuilder()
              .setCustomId(`servertype_${key}`)
              .setLabel(type.name)
              .setStyle(ButtonStyle.Primary)
          )
        );

      const embed = new EmbedBuilder()
        .setTitle('Server-Erstellung')
        .setDescription('Wähle den Typ des Servers, den du erstellen möchtest:')
        .setColor('#007bff');

      return interaction.reply({
        embeds: [embed],
        components: [row],
        ephemeral: true
      });
    }

    ticketCommands.handleCommand(interaction);
    statsCommands.handleCommand(interaction);
    economyCommands.handleCommand(interaction);
    advancedTicketSystem.handleCommand(interaction);
    serverStatus.handleCommand(interaction);
    eventScheduler.handleCommand(interaction);
    pollCreator.handleCommand(interaction);
    roleHierarchy.handleCommand(interaction);
    customCommands.handleCommand(interaction);
    prefixSettings.handleCommand(interaction);
    warningSystem.handleCommand(interaction);
    activityTracker.handleCommand(interaction);
    welcomeMessages.handleCommand(interaction);
    voiceManager.handleCommand(interaction);
    messageScheduler.handleCommand(interaction);
    channelCleanup.handleCommand(interaction);
    messageArchive.handleCommand(interaction);
    categoryManager.handleCommand(interaction);
    verificationLevels.handleCommand(interaction);
    statsGraphs.handleCommand(interaction);
    codeReviewBot.handleCommand(interaction);
    reportBot.handleCommand(interaction);

    if (interaction.commandName === 'dashboard') {
      dashboard.handleDashboardCommand(interaction);
    }
    if (interaction.commandName === 'verify') {
      verificationSystem.handleCommand(interaction);
    }
    if (interaction.commandName === 'filter') {
      messageFilter.handleCommand(interaction);
    }

    return;
  }

  if (interaction.isButton()) {
    if (interaction.customId.startsWith('servertype_')) {
      const serverType = interaction.customId.split('_')[1];

      userRegistrationState.set(interaction.user.id, {
        step: 'email',
        data: { serverType },
        messageId: null
      });

      const embed = new EmbedBuilder()
        .setTitle('Server-Erstellung')
        .setDescription(`Du hast ${SERVER_TYPES[serverType].name} ausgewählt.\n\nBitte gib deine E-Mail-Adresse ein:`)
        .setColor('#007bff')
        .setFooter({ text: 'Schritt 1 von 3: E-Mail' });

      return interaction.update({
        embeds: [embed],
        components: []
      });
    }

    ticketSystem.handleTicketCreate(interaction);
    ticketSystem.handleTicketClose(interaction);
    dashboard.handleRefreshButton(interaction);
    advancedTicketSystem.handleButton(interaction);
    pollCreator.handleButton(interaction);
    voiceManager.handleButton(interaction);
    messageFilter.handleButton(interaction);
    verificationSystem.handleButton(interaction);
    serverStatus.handleButton(interaction);
    codeReviewBot.handleButton(interaction);
    reportBot.handleButton(interaction);

    return;
  }

  if (interaction.isModalSubmit()) {
    advancedTicketSystem.handleModalSubmit(interaction);
    eventScheduler.handleModalSubmit(interaction);
    pollCreator.handleModalSubmit(interaction);
    warningSystem.handleModalSubmit(interaction);
    customCommands.handleModalSubmit(interaction);
    welcomeMessages.handleModalSubmit(interaction);
    return;
  }

  if (interaction.isStringSelectMenu()) {
    advancedTicketSystem.handleSelectMenu(interaction);
    return;
  }

  if (interaction.isUserSelect()) {
    advancedTicketSystem.handleUserSelect(interaction);
    return;
  }
});

client.on('messageReactionAdd', async (reaction, user) => {
  roleManager.handleReaction(reaction, user, true);
  pollCreator.handleReaction(reaction, user, true);
});

client.on('messageReactionRemove', async (reaction, user) => {
  roleManager.handleReaction(reaction, user, false);
  pollCreator.handleReaction(reaction, user, false);
});

client.on('voiceStateUpdate', async (oldState, newState) => {
  tempVoiceChannels.handleVoiceStateUpdate(oldState, newState);
  activityTracker.handleVoiceStateUpdate(oldState, newState);
});

client.on('messageCreate', async (message) => {
  if (message.author.bot) return;

  messageFilter.checkMessage(message);
  activityTracker.trackMessage(message);
  messageLogger.trackMessage(message);
  verificationSystem.handleMessage(message);

  const userState = userRegistrationState.get(message.author.id);
  if (userState) {
    if (message.channelId !== SERVER_CREATION_CHANNEL_ID) return;

    try {
      await message.delete();
    } catch (error) {
      console.error('Fehler beim Löschen der Nachricht:', error);
    }

    switch (userState.step) {
      case 'email':
        if (await handleEmailInput(message, userState) === false) return;
        break;
      case 'username':
        if (await handleUsernameInput(message, userState) === false) return;
        break;
      case 'password':
        const { processingMsg } = await handlePasswordInput(message, userState);
        await processServerCreation(message, userState, processingMsg);
        break;
    }
    return;
  }

  customCommands.handleMessage(message);
});

// --- Webhook Server for Code Review ---
const http = require('http');
const WEBHOOK_PORT = parseInt(process.env.CODE_REVIEW_WEBHOOK_PORT) || 3000;
const webhookServer = http.createServer(async (req, res) => {
  if (req.method === 'GET' && req.url === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'ok',
      service: 'discord-service',
      discord: DISCORD_SERVICE_DISABLED || !DISCORD_TOKEN ? 'disabled' : 'enabled'
    }));
  } else if (req.method === 'POST' && req.url === '/webhook/github') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', async () => {
      try {
        const parsed = JSON.parse(body);
        req.body = parsed;
        await codeReviewBot.handleWebhook(req, res);
      } catch (e) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Invalid JSON' }));
      }
    });
  } else {
    res.writeHead(404);
    res.end();
  }
});
webhookServer.listen(WEBHOOK_PORT, () => {
  console.log(`[Webhook] GitHub webhook server listening on port ${WEBHOOK_PORT}`);
});

// --- Discord Bot Login ---
if (DISCORD_SERVICE_DISABLED || !DISCORD_TOKEN || DISCORD_TOKEN === 'your_discord_bot_token_here') {
  console.log('[Discord] Bot login disabled; webhook and health endpoints remain available.');
} else {
  client.login(DISCORD_TOKEN).catch((error) => {
    console.error('[Discord] Login failed:', error.message);
    process.exitCode = 1;
  });
}
