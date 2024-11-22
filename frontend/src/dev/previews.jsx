import { ComponentPreview, Previews } from "@react-buddy/ide-toolbox";
import { PaletteTree } from "./palette";
import Setting from "../Setting";
import Navigator from "../PermanentDrawer";
import PermanentDrawer from "../PermanentDrawer";

const ComponentPreviews = () => {
  return (
    <Previews palette={<PaletteTree />}>
      <ComponentPreview path="/Setting">
        <Setting />
      </ComponentPreview>
      <ComponentPreview path="/Drawer">
        <Navigator />
      </ComponentPreview>
      <ComponentPreview path="/PermanentDrawer">
        <PermanentDrawer />
      </ComponentPreview>
    </Previews>
  );
};

export default ComponentPreviews;