import { ComponentPreview, Previews } from "@react-buddy/ide-toolbox";
import { PaletteTree } from "./palette";
import DynamicSetting from "../ValueAdapter";
import Navigator from "../PermanentDrawer";
import PermanentDrawer from "../PermanentDrawer";
import ValueAdapter from "../ValueAdapter";

const ComponentPreviews = () => {
  return (
    <Previews palette={<PaletteTree />}>
      <ComponentPreview path="/Setting">
        <DynamicSetting />
      </ComponentPreview>
      <ComponentPreview path="/Drawer">
        <Navigator />
      </ComponentPreview>
      <ComponentPreview path="/PermanentDrawer">
        <PermanentDrawer />
      </ComponentPreview>
      <ComponentPreview path="/ValueAdapter">
        <ValueAdapter />
      </ComponentPreview>
    </Previews>
  );
};

export default ComponentPreviews;
