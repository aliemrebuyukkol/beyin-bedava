using UnityEditor;
using UnityEditor.SceneManagement;

public static class PulseGateScene
{
    [MenuItem("Beyin-Bedava/Open Pulse Gate")]
    public static void Open()
    {
        if (EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo())
            EditorSceneManager.NewScene(NewSceneSetup.DefaultGameObjects, NewSceneMode.Single);
    }
}
