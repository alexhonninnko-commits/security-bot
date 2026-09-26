import { logger } from '../utils/logger.js';

export const botConfig = {
  // =========================
  // BOT PRESENCE (what users see under the bot name)
  // =========================
  // `status` options:
  // - "online"    = green dot
  // - "idle"      = yellow moon
  // - "dnd"       = red do-not-disturb
  // - "invisible" = appears offline
  presence: {
    // Current online state shown on Discord.
    status: "online",

    // Activity lines shown under the bot name.
    // `type` number mapping from Discord:
    // 0 = Playing
    // 1 = Streaming
    // 2 = Listening
    // 3 = Watching
    // 4 = Custom
    // 5 = Competing
    activities: [
      {
        name: " ", // required by Discord API, not shown in the client
        state: "just in time",     // this is what people actually see
        type: 4,               // Custom
      },
    ],
  },
    
const { Client, GatewayIntentBits, PermissionsBitField, ActionRowBuilder, StringSelectMenuBuilder } = require('discord.js');

const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent,
        GatewayIntentBits.GuildMembers
    ]
});

// Sledování pro anti-spam
const userMessageTimestamps = new Map();

const DEFAULT_ROLES_MSG = `# role

<@&1539241329899474954> - **je vlastník serveru, který rozhoduje, co se na server přidá**

<@&1552268147179135046> - **je člen A-Teamu, který s majitelem dělá změny na serveru a hlídá ho**

<@&1539240450810978364> - **je člen A-Teamu, který může také provádět změny na serveru (na žádost majitele) a hlídá server**

<@&1552391311754133555> - **je člen A-Teamu, který testuje, zda všechno funguje**

<@&1549866576029814784> - **je role pro členy, kteří jsou aktivní na serveru a ve voice chatu (VC)**

<@&1539242304013992048> - **je role, kterou mají všichni na serveru**

<@&1543385078992871524> / <@&1543385813943984239> - **je pro členy, kteří si o roli požádají**

<@&1540028254885257256> / <@&1540028432614817862> / <@&1540028872312225914> / <@&1540028968273449002> / <@&1553041371986927657> - **je pro členy, kteří si požádají o barvu přezdívky na serveru**

<@&1553032262696566915> / <@&1553032409073586186> - **je pro členy, kteří si požádají o zobrazení svého věku**

<@&1549872649877069924> - **je pro členy, kteří dají serveru Server Boost**`;

client.once('ready', () => {
    console.log(`[BOT] Přihlášen jako: ${client.user.tag} (ID: ${client.user.id})`);
});

client.on('messageCreate', async (message) => {
    if (message.author.bot || !message.guild) return;

    if (message.member.permissions.has(PermissionsBitField.Flags.Administrator)) {
        await handleCommands(message);
        return;
    }

    const contentLower = message.content.toLowerCase();

    // 1. Anti-Link
    if (contentLower.includes("http://") || contentLower.includes("https://") || contentLower.includes("discord.gg/")) {
        try {
            await message.delete();
            const warning = await message.channel.send(`${message.author}, posílání odkazů je zakázáno!`);
            setTimeout(() => warning.delete().catch(() => {}), 5000);
            return;
        } catch (err) {
            console.error("Chyba mazání odkazu:", err);
        }
    }

    // 2. Anti-Spam
    const userId = message.author.id;
    const now = Date.now();
    if (!userMessageTimestamps.has(userId)) {
        userMessageTimestamps.set(userId, []);
    }
    let timestamps = userMessageTimestamps.get(userId);
    timestamps.push(now);
    timestamps = timestamps.filter(t => now - t <= 5000);
    userMessageTimestamps.set(userId, timestamps);

    if (timestamps.length > 5) {
        try {
            await message.delete();
            const warning = await message.channel.send(`${message.author}, nepřestávej spamovat!`);
            setTimeout(() => warning.delete().catch(() => {}), 5000);
            return;
        } catch (err) {
            console.error("Chyba mazání spamu:", err);
        }
    }

    await handleCommands(message);
});

async function handleCommands(message) {
    if (!message.content.startsWith('!')) return;

    const args = message.content.slice(1).trim().split(/ +/);
    const command = args.shift().toLowerCase();

    if (command === 'setup_roles') {
        if (!message.member.permissions.has(PermissionsBitField.Flags.Administrator)) {
            return message.reply("Na tento příkaz nemáš práva!");
        }

        try {
            // Menu pro barvy
            const rowColor = new ActionRowBuilder().addComponents(
                new StringSelectMenuBuilder()
                    .setCustomId('select_color_role')
                    .setPlaceholder('🎨 Vyber si barvu jména...')
                    .addOptions([
                        { label: 'Červená', value: '1540028254885257256', emoji: '🔴' },
                        { label: 'Modrá', value: '1540028432614817862', emoji: '🔵' },
                        { label: 'Zelená', value: '1540028872312225914', emoji: '🟢' },
                        { label: 'Fialová', value: '1540028968273449002', emoji: '🟣' },
                        { label: 'Žlutá', value: '1553041371986927657', emoji: '🟡' },
                    ])
            );

            // Menu pro věk
            const rowAge = new ActionRowBuilder().addComponents(
                new StringSelectMenuBuilder()
                    .setCustomId('select_age_role')
                    .setPlaceholder('🎂 Vyber si svůj věk...')
                    .addOptions([
                        { label: '13-17+', value: '1553032262696566915', emoji: '🔞' },
                        { label: '18+', value: '1553032409073586186', emoji: '🔞' },
                    ])
            );

            // Odeslání zprávy s textem a oběma menu
            await message.channel.send({
                content: DEFAULT_ROLES_MSG + "\n\n👇 **Vyber si své role v menu níže:**",
                components: [rowColor, rowAge]
            });

            await message.delete().catch(() => {});
        } catch (err) {
            console.error("Chyba při odesílání rolí:", err);
            message.channel.send("Nastala chyba při vytváření zprávy s rolemi.");
        }
    }
}

// Reakce na interakci s menu (barvy i věk)
client.on('interactionCreate', async (interaction) => {
    if (!interaction.isStringSelectMenu()) return;
    
    if (interaction.customId === 'select_color_role' || interaction.customId === 'select_age_role') {
        const roleId = interaction.values[0];
        const role = interaction.guild.roles.cache.get(roleId);

        if (!role) {
            return interaction.reply({ content: "⚠️ Role na serveru nebyla nalezena.", ephemeral: true });
        }

        try {
            if (interaction.member.roles.cache.has(roleId)) {
                await interaction.member.roles.remove(roleId);
                await interaction.reply({ content: `❌ Role **${role.name}** ti byla odebrána.`, ephemeral: true });
            } else {
                await interaction.member.roles.add(roleId);
                await interaction.reply({ content: `✅ Role **${role.name}** ti byla přidána!`, ephemeral: true });
            }
        } catch (err) {
            console.error(err);
            await interaction.reply({ content: "❌ Nemám oprávnění spravovat tuto roli! Ujisti se, že botova role je v seznamu rolí výše než role, kterou se snaží přidat.", ephemeral: true });
        }
    }
});

client.login(process.env.DISCORD_TOKEN);
