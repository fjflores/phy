# GUI

`phy.gui` provides generic Qt-based GUI components. You don't need to know Qt to use `phy.gui`, although it might help.

## Creating a Qt application

You need to create a Qt application before creating and using GUIs. There is a single Qt application object in a Python interpreter.

In IPython (console or notebook), you can just use the following magic command before doing anything Qt-related:

```python
>>> %gui qt
```

In other situations, like in regular Python scripts, you need to:

* Call `phy.gui.create_app()` once, before you create a GUI.
* Call `phy.gui.run_app()` to launch your application. This blocks the Python interpreter and runs the Qt event loop. Generally, when this call returns, the application exits.

For interactive use and explorative work, it is highly recommended to use IPython, for example with a Jupyter Notebook.

## Creating a GUI

phy provides a **GUI**, a main window with dockable widgets (`QMainWindow`). By default, a GUI is empty, but you can add views. A view is any Qt widget or a matplotlib or VisPy canvas.

Let's create an empty GUI:

```python
>>> from phy.gui import GUI
>>> gui = GUI(position=(400, 200), size=(600, 400))
>>> gui.show()
```

## Adding a visualization

We can add any Qt widget with `gui.add_view(widget)`, as well as visualizations with VisPy or matplotlib (which are fully compatible with Qt and phy).

### With VisPy

The `gui.add_view()` method accepts any VisPy canvas. For example, here we add an empty VisPy window:

```python
>>> from vispy.app import Canvas
>>> from vispy import gloo
...
>>> c = Canvas()
...
>>> @c.connect
... def on_draw(e):
...     gloo.clear('purple')
...
>>> gui.add_view(c)
<phy.gui.gui.DockWidget at 0x7f717087b0d8>
```

We can now dock and undock our widget from the GUI. This is particularly convenient when there are many widgets.

### With matplotlib

Here we add a matplotlib figure to our GUI:

```python
>>> import numpy as np
>>> import matplotlib.pyplot as plt
...
>>> f = plt.figure()
>>> ax = f.add_subplot(111)
>>> t = np.linspace(-10., 10., 1000)
>>> ax.plot(t, np.sin(t))
>>> gui.add_view(f)
<phy.gui.gui.DockWidget at 0x7f717011dee8>
```

## Adding an HTML widget

phy provides an `HTMLWidget` component which allows you to create widgets in HTML. This is just a `QWebView` with some user-friendly facilities.

First, let's create a standalone HTML widget:

```python
>>> from phy.gui import HTMLWidget
>>> widget = HTMLWidget()
>>> widget.set_body("Hello world!")
>>> widget.show()
```

Now that our widget is created, let's add it to the GUI:

```python
>>> gui.add_view(widget)
<phy.gui.gui.DockWidget at 0x7f7e780b3288>
```

You'll find in the API reference other methods to edit the styles, scripts, header, and body of the HTML widget.

### Table

phy also provides a `Table` widget written in HTML and Javascript (using the [tablesort](https://github.com/tristen/tablesort) Javascript library). This widget shows a table of items, where every item (row) has an id, and every column is defined as a function `id => string`, the string being the contents of a row's cell in the table. The table can be sorted by every column.

One or several items can be selected by the user. The `select` event is raised when rows are selected. Here is a complete example:

```python
>>> from phy.gui import Table
>>> table = Table()
...
>>> # We add a column in the table.
... @table.add_column
... def name(id):
...     # This function takes an id as input and returns a string.
...     return "My id is %d" % id
...
>>> # Now we add some rows.
... table.set_rows([2, 3, 5, 7])
...
>>> # We print something when items are selected.
... @table.connect_
... def on_select(ids):
...     # NOTE: we use `connect_` and not `connect`, because `connect` is
...     # a Qt method associated to every Qt widget, and `Table` is a subclass
...     # of `QWidget`. Using `connect_` ensures that we're using phy's event
...     # system, not Qt's.
...     print("The items %s have been selected." % ids)
...
>>> table.show()
The items [3] have been selected.
The items [3, 5] have been selected.
```

### Interactivity with Javascript

We can use Javascript in an HTML widget, and we can make Python and Javascript communicate.

```python
>>> from phy.gui import HTMLWidget
>>> widget = HTMLWidget()
>>> widget.set_body('<div id="mydiv"></div>')
>>> # We can execute Javascript code from Python.
... widget.eval_js("document.getElementById('mydiv').innerHTML='hello'")
>>> widget.show()
>>> gui.add_view(widget)
<phy.gui.gui.DockWidget at 0x7f7e780b3438>
```

You can use `widget.eval_js()` to evaluate Javascript code from Python. Conversely, you can use `widget.some_method()` from Javascript, where `some_method()` is a method implemented in your widget (which should be a subclass of `HTMLWidget`).

## Other GUI methods

Let's display the list of views in the GUI:

```python
>>> gui.list_views()
[<phy.gui.gui.DockWidget at 0x7f7e81466dc8>,
 <phy.gui.gui.DockWidget at 0x7f7e800da708>,
 <phy.gui.gui.DockWidget at 0x7f7e780b3288>,
 <phy.gui.gui.DockWidget at 0x7f7e780b3438>]
```

The following method allows you to check how many views of each class there are:

```python
>>> gui.view_count()
```

Use the following property to change the status bar:

```python
>>> gui.status_message = "Hello world"
```

Finally, the following methods allow you to save/restore the state of the GUI and the widgets:

```python
>>> gs = gui.save_geometry_state()
```

```python
>>> gui.restore_geometry_state(gs)
```

The object `gs` is a JSON-serializable Python dictionary.

## Adding actions

An **action** is a Python function that the user can run from the menu bar or with a keyboard shortcut. You can create an `Actions` object to specify a list of actions attached to a GUI.

```python
>>> from phy.gui import Actions
>>> actions = Actions(gui)
...
>>> @actions.add(shortcut='ctrl+h')
... def hello():
...     print("Hello world!")
```

Now, if you press *Ctrl+H* in the GUI, you'll see `Hello world!` printed in the console.

Once an action is added, you can call it with `actions.hello()` where `hello` is the name of the action. By default, this is the name of the associated function, but you can also specify the name explicitly with the `name=...` keyword argument in `actions.add()`.

You'll find more details about `actions.add()` in the API reference. For example, use the `menu='MenuName'` keyword argument to add the action to a menu in the menu bar.

Every GUI comes with a `default_actions` property which implements actions always available in GUIs:

```python
>>> gui.default_actions
<Actions ['exit', 'show_shortcuts']>
```

For example, the following action shows the shortcuts of all actions attached to the GUI:

```python
>>> gui.default_actions.show_shortcuts()

Keyboard shortcuts for GUI
enable_snippet_mode                     : :
exit                                    : ctrl+q
hello                                   : ctrl+h
show_shortcuts                          : f1, h
```

You can create multiple `Actions` instance for a single GUI, which allows you to separate between different sets of actions.

## Snippets

The GUI provides a convenient system to quickly execute actions without leaving one's keyboard. Inspired by console-based text editors like *vim*, it is enabled by pressing `:` on the keyboard. Once this mode is enabled, what you type is displayed in the status bar. Then, you can call a function by typing its name or its alias. You can also use arguments to the actions, using a special syntax. Here is an example.

```python
>>> @actions.add(alias='c')
... def select(ids, obj):
...     print("Select %s with %s" % (ids, obj))
```

Now, pressing `:c 3-6 hello` followed by the `Enter` keystroke displays `Select [3, 4, 5, 6] with hello` in the console.

By convention, multiple arguments are separated by spaces, sequences of numbers are given either with `2,3,5,7` or `3-6` for consecutive numbers. If an alias is not specified when adding the action, you can always use the full action's name.

## GUI plugins

To create a specific GUI, you implement functionality in components and create GUI plugins to allow users to activate these components in their GUI. You can also specify the list of default plugins.

You create a GUI with the function `gui = create_gui(name, model=model, plugins=plugins)`. The model provides the data while the list of plugins defines the functionality of the GUI.

Plugins create views and actions and have full control on the GUI. Also, they can register objects or functions with `gui.register(obj, name='my_object')`. Other plugins can then retrieve these objects with `gui.request(name)`. This is how plugins can communicate. This function returns `None` if the object is not available.

Note that the order of how plugins are attached matters, since you can only request components that have been registered in the previously-attached  plugins.

To create a GUI plugin, just define a class deriving from `IPlugin` and implementing `attach_to_gui(gui, model=None, state=None)`.

## GUI state

The **GUI state** is a special Python dictionary that holds info and parameters about a particular GUI session, like its position and size, the positions of the widgets, and other user preferences. This state is automatically persisted to disk (in JSON) in the config directory (passed as a parameter in the `create_gui()` function). By default, this is `~/.phy/gui_name/state.json`.

The GUI state is a `Bunch` instance, which derives from `dict` to support the additional `bunch.name` syntax.

Plugins can simply add fields to the GUI state and it will be persisted. There are special methods for GUI parameters: `state.save_gui_params()` and `state.load_gui_params()`.


## Example

In this example we'll create a GUI plugin and show how to activate it.

```python
>>> from phy import IPlugin
>>> from phy.gui import GUI, HTMLWidget, create_app, run_app, create_gui
>>> from phy.utils import Bunch
```

```python
>>> class MyComponent(IPlugin):
...     def attach_to_gui(self, gui, model=None, state=None):
...         # We create a widget.
...         view = HTMLWidget()
...         view.set_body("Hello %s!" % model.name)
...         view.show()
...         gui.add_view(view)
DEBUG:phy.utils.plugin:Register plugin `MyComponent`.
```

```python
>>> gui = create_gui('MyGUI', model=Bunch(name='world'), plugins=['MyComponent'])
DEBUG:phy.gui.gui:The GUI state file `/Users/cyrille/.phy/MyGUI/state.json` doesn't exist.
DEBUG:phy.gui.gui:Attach plugin `MyComponent` to MyGUI.
```

```python
>>> gui.show()
DEBUG:phy.gui.gui:Save the GUI state to `/Users/cyrille/.phy/MyGUI/state.json`.
```

This opens a GUI showing `Hello world!`.