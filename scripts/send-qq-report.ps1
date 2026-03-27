param(
    [Parameter(Mandatory = $true)]
    [string]$Message,
    [string]$OpenId = "4193BD194E319F7E000AF005F82E06CE",
    [string]$AppId = "1903690011",
    [string]$ClientSecret = "b7RYR7Zt0ua3IJ6g"
)

$ErrorActionPreference = "Stop"
$env:QQBOT_REPORT_MESSAGE = $Message
$env:QQBOT_REPORT_OPENID = $OpenId
$env:QQBOT_REPORT_APPID = $AppId
$env:QQBOT_REPORT_SECRET = $ClientSecret

@"
const { getAccessToken, sendProactiveC2CMessage } = require('C:/Users/25472/.openclaw/extensions/openclaw-qqbot/dist/src/api.js');
(async () => {
  const token = await getAccessToken(process.env.QQBOT_REPORT_APPID, process.env.QQBOT_REPORT_SECRET);
  const result = await sendProactiveC2CMessage(
    token,
    process.env.QQBOT_REPORT_OPENID,
    process.env.QQBOT_REPORT_MESSAGE
  );
  console.log(JSON.stringify(result, null, 2));
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
"@ | node -
