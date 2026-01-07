# Animation Patterns

Patterns for MUI + Framer Motion integration.

---

## MUI + Framer Motion Integration

### Technique 1: MUI `component` Prop (Recommended)

Use MUI's `component` prop to inject motion capabilities directly:

```jsx
import { Button, Box, Card } from '@mui/material';
import { motion } from 'framer-motion';

// Button with motion
<Button
  component={motion.button}
  variant="contained"
  whileHover={{ scale: 1.05 }}
  whileTap={{ scale: 0.95 }}
>
  Click Me
</Button>

// Box with motion
<Box
  component={motion.div}
  initial={{ opacity: 0 }}
  animate={{ opacity: 1 }}
  sx={{ p: 2 }}
>
  Content
</Box>
```

**Match motion type to element:**

| MUI Component | Motion Type |
|---------------|-------------|
| Button | `motion.button` |
| Box, Stack, Grid, Paper | `motion.div` |
| Icon (SVG) | `motion.svg` |
| Typography | `motion.p` or `motion.span` |

### Technique 2: Wrap MUI with motion()

Create reusable motion-enhanced MUI components:

```jsx
import { Grid, Card } from '@mui/material';
import { motion } from 'framer-motion';

const MotionGrid = motion(Grid);
const MotionCard = motion(Card);

<MotionCard
  initial={{ opacity: 0 }}
  animate={{ opacity: 1 }}
  whileHover={{ y: -4 }}
>
  Content
</MotionCard>
```

**Anti-Pattern:** Don't wrap MUI components in `<motion.div>`. Use `component` prop or `motion()` wrapper instead.

---

## Pattern 1: Staggered Children

**When to Apply:** Animating lists, grids, or multiple cards appearing in sequence.

```jsx
// Parent container animation
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      when: "beforeChildren",
      staggerChildren: 0.1
    }
  }
};

// Child item animation
const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: { type: "spring", bounce: 0.4 }
  }
};

// Usage
<motion.div
  initial="hidden"
  animate="visible"
  variants={containerVariants}
>
  {items.map((item) => (
    <motion.div key={item.id} variants={itemVariants}>
      <Card>{item.content}</Card>
    </motion.div>
  ))}
</motion.div>
```

---

## Pattern 2: Propagation

**When to Apply:** Hover effects that cascade to child elements.

```jsx
// Only parent defines animate prop
<motion.div initial="initial" whileHover="hover">
  {/* Children only define variants - no animate prop needed */}
  <motion.div variants={{
    initial: { scale: 1 },
    hover: { scale: 1.1 }
  }} />
  <motion.div variants={{
    initial: { opacity: 0.5 },
    hover: { opacity: 1 }
  }} />
</motion.div>
```

**Key Point:** Variants "flow down" from parent to children without children needing `animate` prop.

---

## Pattern 3: AnimatePresence (Exit Animations)

**When to Apply:** Modals, toasts, conditional content that needs graceful exit.

```jsx
import { AnimatePresence, motion } from 'framer-motion';

<AnimatePresence mode="wait">
  {isOpen && (
    <motion.div
      key="modal"
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      transition={{ type: "spring", duration: 0.3 }}
    >
      <Card>Modal Content</Card>
    </motion.div>
  )}
</AnimatePresence>
```

**Key Point:** AnimatePresence tracks which motion component renders across state changes.

---

## Pattern 4: Layout Animations

**When to Apply:** Smooth transitions when elements reorder, resize, or change position.

```jsx
// Simple layout animation
<motion.div layout>
  {/* CSS changes (width, position, flex) animate smoothly */}
</motion.div>

// Shared layout between components
<motion.div layoutId="shared-element">
  {/* Element animates between positions */}
</motion.div>

// List reordering
{items.map((item) => (
  <motion.div key={item.id} layout>
    <ListItem>{item.name}</ListItem>
  </motion.div>
))}
```

**Key Point:** Use `layout` sparingly - only on elements that actually change position.

---

## Pattern 5: Gesture Feedback

**When to Apply:** Interactive hover, tap, drag feedback.

```jsx
<motion.div
  whileHover={{
    scale: 1.05,
    boxShadow: "0 10px 30px rgba(0,0,0,0.2)"
  }}
  whileTap={{ scale: 0.95 }}
  transition={{ type: "spring", stiffness: 400, damping: 17 }}
>
  <Card>Interactive Card</Card>
</motion.div>

// Draggable element
<motion.div
  drag="x"
  dragConstraints={{ left: -100, right: 100 }}
  dragElastic={0.2}
>
  Drag me
</motion.div>
```

---

## Transition Reference

### Spring (Natural, Bouncy)

```jsx
transition: {
  type: "spring",
  stiffness: 400,  // Higher = snappier
  damping: 17,     // Higher = less bounce
  mass: 1          // Higher = heavier feel
}
```

**Use for:** Buttons, cards, interactive elements (feels natural)

### Tween (Controlled, Predictable)

```jsx
transition: {
  type: "tween",
  duration: 0.3,
  ease: "easeInOut"  // or "anticipate", "circOut", etc.
}
```

**Use for:** Modals, fades, progress indicators (predictable timing)

---

## Reusable Components

### Animated Card

```jsx
const MotionCard = motion(Card);

const AnimatedCard = memo(({ title, icon: Icon, children, delay = 0 }) => (
  <MotionCard
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ type: "spring", delay, stiffness: 100 }}
    whileHover={{ y: -4, boxShadow: "0 12px 24px rgba(0,0,0,0.15)" }}
  >
    <CardHeader
      avatar={
        <motion.div whileHover={{ rotate: 5, scale: 1.1 }}>
          <Avatar><Icon /></Avatar>
        </motion.div>
      }
      title={title}
    />
    <CardContent>{children}</CardContent>
  </MotionCard>
));
```

### Page Transition Wrapper

```jsx
const PageTransition = ({ children }) => (
  <motion.div
    initial={{ opacity: 0, x: -20 }}
    animate={{ opacity: 1, x: 0 }}
    exit={{ opacity: 0, x: 20 }}
    transition={{ duration: 0.3 }}
  >
    {children}
  </motion.div>
);
```

---

## Performance Best Practices

1. **Memoize animated sub-components** - Prevents unnecessary re-renders
2. **Use `layout` sparingly** - Only on elements that actually change position
3. **Prefer transform properties** - `scale`, `rotate`, `x`, `y` over `width`, `height`
4. **Use variants pattern** - For state-based animations instead of inline objects
5. **Unique keys on list items** - Required for AnimatePresence tracking

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Wrap MUI in `<motion.div>` | Use `component={motion.div}` prop |
| Animate width/height directly | Use `scale` or `layout` |
| Heavy animations on frequently re-rendered components | Memoize or use CSS transitions |
| `initial`/`animate` on list items without `key` | Always use unique keys |
| Multiple AnimatePresence wrappers | Single AnimatePresence at route level |
