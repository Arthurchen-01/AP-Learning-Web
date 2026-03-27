param(
  [Parameter(Mandatory = $true)]
  [string]$UserName,

  [Parameter(Mandatory = $true)]
  [string]$UserEmail,

  [Parameter(Mandatory = $true)]
  [string]$RemoteUrl
)

$repo = Split-Path -Parent $MyInvocation.MyCommand.Path

git -C $repo config user.name $UserName
git -C $repo config user.email $UserEmail
git -C $repo commit -m "Initial private upload prep"
git -C $repo remote remove origin 2>$null
git -C $repo remote add origin $RemoteUrl
git -C $repo push -u origin main
