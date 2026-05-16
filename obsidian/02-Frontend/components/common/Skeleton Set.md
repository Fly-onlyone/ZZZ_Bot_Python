---
tags: [frontend, components, common]
---

# Skeleton Set

> Per-route Suspense skeletons that match each page's layout while data loads.

## How it works
`Skeleton/index.js` is a barrel that re-exports eight named skeletons, one per major route or content section: `BackupSkeleton`, `HuntSkeleton`, `LogsSkeleton`, `MissionSkeleton`, `RedeemSkeleton`, `RunningStatusSkeleton`, `SettingsSkeleton`, `ShoppingSkeleton`. Each file renders MUI `Skeleton` shapes laid out to mimic the real component's grid (cards, table rows, toolbars), giving users visual continuity during `React.lazy` chunk loads and TanStack Query fetches. Routes wire them as `<Suspense fallback={<XxxSkeleton/>}>` boundaries.

## Source
- `frontend/src/components/common/Skeleton/index.js` — barrel
- `frontend/src/components/common/Skeleton/{Backup,Hunt,Logs,Mission,Redeem,RunningStatus,Settings,Shopping}Skeleton.jsx` — implementations

## Depends on
- [[MUI]] — `Skeleton` primitive

## Used by
- [[PermanentDrawer Router]] — route-level Suspense fallbacks
- [[Mission Section]], [[Hunt Section]], [[Running Status Section]] — content-level fallbacks

## See also
- [[_index]]
- [[EmptyState]]
